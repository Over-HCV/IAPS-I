"""Training Worker - Background training execution"""

from datetime import datetime
import threading
from typing import Any

from models.pytorch.cnn_builder import CustomCNNBuilder
from models.pytorch.transfer import TransferLearningBuilder
from models.pytorch.transformer import TransformerBuilder
from state.persistence import (
    get_dataset_config_from_file,
    get_experiment_from_file,
    get_model_from_file,
    get_training_from_file,
    write_experiment_update,
)
from state.workflow import get_session_id, update_experiment
import torch
from training.dataset import create_dataloaders
from training.engine import TrainingEngine
from training.optimizers import create_criterion, create_optimizer, create_scheduler
from utils.checkpoint_manager import CheckpointManager

# Global registry for active training engines
_active_engines: dict[str, TrainingEngine] = {}
_training_threads: dict[str, threading.Thread] = {}


def build_model(model_config: dict[str, Any]) -> torch.nn.Module:
    """Build PyTorch model from config."""
    model_type = model_config.get("model_type")

    if model_type == "Custom CNN":
        builder = CustomCNNBuilder(model_config)
    elif model_type == "Transfer Learning":
        builder = TransferLearningBuilder(model_config)
    elif model_type == "Transformer":
        builder = TransformerBuilder(model_config)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    return builder.build()


def _run_training(session_id: str, experiment_id: str):
    """Run training in background thread.

    Uses file-based I/O instead of st.session_state since
    session_state is thread-local and not accessible from background threads.
    """
    try:
        # Get experiment from file (thread-safe)
        experiment = get_experiment_from_file(session_id, experiment_id)
        if not experiment:
            print(
                f"[Training] Experiment {experiment_id} not found in session {session_id}"
            )
            return

        print(
            f"\n[Training] Starting experiment: {experiment.get('name', experiment_id)}"
        )

        # Get configs from file (thread-safe)
        model_entry = get_model_from_file(session_id, experiment.get("model_id"))
        training_entry = get_training_from_file(
            session_id, experiment.get("training_id")
        )
        dataset_config = get_dataset_config_from_file(session_id)

        if not model_entry:
            raise ValueError("Model config not found")
        if not training_entry:
            raise ValueError("Training config not found")

        model_config = model_entry.get("config", model_entry)
        training_config = training_entry.get("config", training_entry)

        print(
            f"[Training] Model: {model_entry.get('name')} ({model_config.get('model_type')})"
        )
        print(f"[Training] Training config: {training_entry.get('name')}")

        # Determine device
        device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "mps"
            if torch.backends.mps.is_available()
            else "cpu"
        )
        print(f"[Training] Using device: {device}")

        # Build model
        print("[Training] Building model...")
        model = build_model(model_config)
        model = model.to(device)

        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(
            f"[Training] Parameters: {total_params:,} total, {trainable_params:,} trainable"
        )

        # Create dataloaders
        print("[Training] Creating dataloaders...")
        dataloaders, class_names, class_weights = create_dataloaders(
            dataset_config,
            training_config,
            num_workers=4,
        )

        # Store max_epochs in experiment for progress display
        epochs = training_config.get("epochs", 100)
        write_experiment_update(session_id, experiment_id, {"max_epochs": epochs})

        # Create optimizer, scheduler, criterion
        optimizer = create_optimizer(model, training_config)
        scheduler = create_scheduler(
            optimizer,
            training_config,
            steps_per_epoch=len(dataloaders["train"]),
        )
        criterion = create_criterion(training_config, class_weights, device)

        # Early stopping
        early_stopping_patience = 0
        if training_config.get("early_stopping"):
            early_stopping_patience = training_config.get("es_patience", 10)

        # Checkpoint manager
        checkpoint_manager = CheckpointManager()

        def checkpoint_callback(epoch: int, metrics: dict, is_best: bool):
            if training_config.get("checkpointing", True):
                checkpoint_manager.save_checkpoint(
                    session_id=experiment_id,
                    model=model,
                    optimizer=optimizer,
                    epoch=epoch,
                    loss=metrics.get("val_loss", 0),
                    metrics=metrics,
                    model_config=model_config,
                    scheduler=scheduler,
                    is_best=is_best,
                )

        # Batch callback for progress updates during epoch
        def batch_callback(batch: int, total: int, metrics: dict):
            write_experiment_update(
                session_id,
                experiment_id,
                {
                    "current_batch": batch,
                    "total_batches": total,
                    "batch_metrics": {
                        "loss": metrics.get("batch_loss", 0),
                        "acc": metrics.get("batch_acc", 0),
                    },
                },
            )

        # Create training engine
        engine = TrainingEngine(
            model=model,
            train_loader=dataloaders["train"],
            val_loader=dataloaders["val"],
            optimizer=optimizer,
            criterion=criterion,
            device=device,
            scheduler=scheduler,
            early_stopping_patience=early_stopping_patience,
            checkpoint_callback=checkpoint_callback,
            batch_callback=batch_callback,
        )

        # Register engine for pause/stop control
        _active_engines[experiment_id] = engine

        # Update callback to sync state with file (thread-safe)
        def update_callback(epoch: int, metrics: dict):
            # Get previous metrics for delta display
            current_exp = get_experiment_from_file(session_id, experiment_id)
            current_metrics = current_exp.get("metrics", {}) if current_exp else {}

            write_experiment_update(
                session_id,
                experiment_id,
                {
                    "current_epoch": epoch,
                    "current_batch": 0,  # Reset batch progress for new epoch
                    "total_batches": 0,
                    "prev_metrics": current_metrics,
                    "metrics": {
                        "train_loss": metrics.get("train_loss", 0),
                        "train_acc": metrics.get("train_acc", 0),
                        "val_loss": metrics.get("val_loss", 0),
                        "val_acc": metrics.get("val_acc", 0),
                        "lr": metrics.get("lr", 0),
                    },
                },
            )

        # Run training
        results = engine.fit(epochs=epochs, update_callback=update_callback)

        # Training complete
        final_metrics = {
            "train_loss": results["history"]["train_loss"][-1]
            if results["history"]["train_loss"]
            else 0,
            "train_acc": results["history"]["train_acc"][-1]
            if results["history"]["train_acc"]
            else 0,
            "val_loss": results["best_val_loss"],
            "val_acc": results["history"]["val_acc"][results["best_epoch"] - 1]
            if results["history"]["val_acc"]
            else 0,
        }

        write_experiment_update(
            session_id,
            experiment_id,
            {
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "current_epoch": results["final_epoch"],
                "best_epoch": results["best_epoch"],
                "duration": results["duration"],
                "metrics": final_metrics,
                "history": results["history"],  # Save full training history for charts
            },
        )

        print(f"[Training] Experiment {experiment_id} completed successfully")

    except Exception as e:
        print(f"[Training] ERROR: {e}")
        import traceback

        traceback.print_exc()
        write_experiment_update(
            session_id,
            experiment_id,
            {
                "status": "failed",
                "error": str(e),
            },
        )

    finally:
        # Cleanup
        if experiment_id in _active_engines:
            del _active_engines[experiment_id]
        if experiment_id in _training_threads:
            del _training_threads[experiment_id]


def start_training(experiment_id: str, session_id: str | None = None):
    """Start training in a background thread.

    Args:
        experiment_id: Experiment ID to train
        session_id: Session ID (if None, gets from st.session_state)
    """
    # Get session_id from Streamlit main thread if not provided
    if session_id is None:
        session_id = get_session_id()

    if not session_id:
        print("[Training] ERROR: No session_id available")
        return

    # Update status (use st.session_state for immediate UI feedback)
    update_experiment(
        experiment_id,
        {
            "status": "training",
            "started_at": datetime.now().isoformat(),
            "current_epoch": 0,
            "metrics": {},
        },
    )

    # Start training thread with session_id
    thread = threading.Thread(
        target=_run_training,
        args=(session_id, experiment_id),
        daemon=True,
    )
    _training_threads[experiment_id] = thread
    thread.start()

    print(
        f"[Training] Started background training for {experiment_id} in session {session_id}"
    )


def stop_training(experiment_id: str):
    """Stop training."""
    if experiment_id in _active_engines:
        _active_engines[experiment_id].stop()
        print(f"[Training] Stopping {experiment_id}")

    update_experiment(
        experiment_id,
        {
            "status": "ready",
            "current_epoch": 0,
            "metrics": {},
        },
    )


def pause_training(experiment_id: str):
    """Pause training."""
    if experiment_id in _active_engines:
        _active_engines[experiment_id].pause()
        print(f"[Training] Pausing {experiment_id}")

    update_experiment(experiment_id, {"status": "paused"})


def resume_training(experiment_id: str):
    """Resume paused training."""
    if experiment_id in _active_engines:
        _active_engines[experiment_id].resume()
        print(f"[Training] Resuming {experiment_id}")

    update_experiment(experiment_id, {"status": "training"})


def is_training_active(experiment_id: str) -> bool:
    """Check if training is active for an experiment."""
    return experiment_id in _active_engines
