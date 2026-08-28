"""Model loading utilities for interpretability."""

from state.persistence import get_model_from_file
from state.workflow import get_experiments, get_session_id
import torch
import torch.nn as nn
from training.worker import build_model
from utils.checkpoint_manager import CheckpointManager


def get_device() -> torch.device:
    """Get the best available device."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def get_completed_experiments() -> list[dict]:
    """Get list of completed experiments."""
    experiments = get_experiments()
    return [exp for exp in experiments if exp.get("status") == "completed"]


def load_experiment_model(exp_id: str) -> tuple[nn.Module, torch.device, dict]:
    """
    Load a trained model from an experiment checkpoint.

    Args:
        exp_id: Experiment ID

    Returns:
        Tuple of (model, device, experiment_dict)
    """
    session_id = get_session_id()

    experiments = get_experiments()
    experiment = next((e for e in experiments if e["id"] == exp_id), None)
    if not experiment:
        raise ValueError(f"Experiment {exp_id} not found")

    model_entry = get_model_from_file(session_id, experiment.get("model_id"))
    if not model_entry:
        raise ValueError(f"Model config not found for experiment {exp_id}")

    model_config = model_entry.get("config", {})

    checkpoint_mgr = CheckpointManager()
    checkpoint_path = checkpoint_mgr.get_best_checkpoint(exp_id)
    if not checkpoint_path:
        raise ValueError(f"No checkpoint found for experiment {exp_id}")

    model = build_model(model_config)
    checkpoint_mgr.load_checkpoint(checkpoint_path, model)

    device = get_device()
    model = model.to(device)
    model.eval()

    return model, device, experiment
