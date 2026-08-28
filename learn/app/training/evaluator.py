"""Test Set Evaluator - Run inference on test set and compute metrics"""

import numpy as np
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
import torch
from training.dataset import create_dataloaders
from training.worker import build_model
from utils.checkpoint_manager import CheckpointManager


def run_test_evaluation(
    experiment_id: str,
    model_config: dict,
    dataset_config: dict,
) -> dict:
    """
    Run inference on test set and compute metrics.

    Args:
        experiment_id: ID of the experiment (used to find checkpoint)
        model_config: Model configuration dict
        dataset_config: Dataset configuration dict

    Returns:
        dict with confusion_matrix, classification_report, per_class_metrics
    """
    device = torch.device(
        "cuda" if torch.cuda.is_available()
        else "mps" if torch.backends.mps.is_available()
        else "cpu"
    )
    print(f"[Evaluator] Using device: {device}")

    # Load best checkpoint
    checkpoint_mgr = CheckpointManager()
    checkpoint_path = checkpoint_mgr.get_best_checkpoint(experiment_id)
    if not checkpoint_path:
        raise ValueError(f"No checkpoint found for {experiment_id}")

    print(f"[Evaluator] Loading checkpoint: {checkpoint_path}")

    # Build model and load weights
    model = build_model(model_config)
    checkpoint_mgr.load_checkpoint(checkpoint_path, model)
    model = model.to(device)
    model.eval()

    # Create test dataloader
    print("[Evaluator] Creating test dataloader...")
    dataloaders, class_names, _ = create_dataloaders(
        dataset_config,
        {"batch_size": 32},
        num_workers=4,
    )
    test_loader = dataloaders["test"]
    print(f"[Evaluator] Test set: {len(test_loader.dataset)} samples")

    # Run inference
    all_preds = []
    all_targets = []

    print("[Evaluator] Running inference...")
    with torch.no_grad():
        for inputs, targets in test_loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            _, predicted = outputs.max(1)

            all_preds.extend(predicted.cpu().numpy())
            all_targets.extend(targets.numpy())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)

    # Compute metrics
    print("[Evaluator] Computing metrics...")
    cm = confusion_matrix(all_targets, all_preds)

    report = classification_report(
        all_targets,
        all_preds,
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )

    precision, recall, f1, support = precision_recall_fscore_support(
        all_targets, all_preds, average=None, zero_division=0
    )

    # Compute overall accuracy
    accuracy = (all_preds == all_targets).sum() / len(all_targets)
    print(f"[Evaluator] Test accuracy: {accuracy*100:.2f}%")

    return {
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "class_names": class_names,
        "per_class": {
            "precision": precision.tolist(),
            "recall": recall.tolist(),
            "f1": f1.tolist(),
            "support": support.tolist(),
        },
        "accuracy": float(accuracy),
        "total_samples": len(all_targets),
    }
