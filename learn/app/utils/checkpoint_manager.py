"""
Checkpoint Manager
Save and load model checkpoints with full training state
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import json
import torch
import torch.nn as nn


class CheckpointManager:
    """Manage model checkpoints with full training state"""

    def __init__(self, checkpoint_dir: str = "checkpoints"):
        """
        Initialize checkpoint manager

        Args:
            checkpoint_dir: Directory to save checkpoints
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        session_id: str,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        epoch: int,
        loss: float,
        metrics: Dict[str, Any],
        model_config: Dict[str, Any],
        scheduler: Optional[Any] = None,
        is_best: bool = False
    ) -> str:
        """
        Save a training checkpoint

        Args:
            session_id: Current session ID
            model: PyTorch model
            optimizer: Optimizer
            epoch: Current epoch
            loss: Current loss
            metrics: Training metrics
            model_config: Model configuration
            scheduler: Learning rate scheduler (optional)
            is_best: Whether this is the best model so far

        Returns:
            Path to saved checkpoint
        """
        # Create session directory
        session_dir = self.checkpoint_dir / session_id
        session_dir.mkdir(exist_ok=True)

        # Generate checkpoint filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_name = f"checkpoint_epoch_{epoch}_{timestamp}.pt"
        checkpoint_path = session_dir / checkpoint_name

        # Prepare checkpoint data
        checkpoint = {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "loss": loss,
            "metrics": metrics,
            "model_config": model_config,
            "timestamp": timestamp,
            "session_id": session_id
        }

        # Add scheduler state if provided
        if scheduler is not None:
            checkpoint["scheduler_state_dict"] = scheduler.state_dict()

        # Save checkpoint
        torch.save(checkpoint, checkpoint_path)

        # If this is the best model, save a copy as 'best_model.pt'
        if is_best:
            best_path = session_dir / "best_model.pt"
            torch.save(checkpoint, best_path)

        # Save metadata
        self._save_metadata(session_dir, checkpoint_path, epoch, loss, metrics)

        return str(checkpoint_path)

    def load_checkpoint(
        self,
        checkpoint_path: str,
        model: nn.Module,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Load a checkpoint

        Args:
            checkpoint_path: Path to checkpoint file
            model: Model to load state into
            optimizer: Optimizer to load state into (optional)
            scheduler: Scheduler to load state into (optional)

        Returns:
            Dictionary with checkpoint metadata
        """
        checkpoint = torch.load(checkpoint_path, map_location=torch.device('cpu'))

        # Load model state
        model.load_state_dict(checkpoint["model_state_dict"])

        # Load optimizer state if provided
        if optimizer is not None and "optimizer_state_dict" in checkpoint:
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

        # Load scheduler state if provided
        if scheduler is not None and "scheduler_state_dict" in checkpoint:
            scheduler.load_state_dict(checkpoint["scheduler_state_dict"])

        return {
            "epoch": checkpoint.get("epoch", 0),
            "loss": checkpoint.get("loss", 0),
            "metrics": checkpoint.get("metrics", {}),
            "model_config": checkpoint.get("model_config", {}),
            "timestamp": checkpoint.get("timestamp", ""),
            "session_id": checkpoint.get("session_id", "")
        }

    def get_latest_checkpoint(self, session_id: str) -> Optional[str]:
        """
        Get the path to the latest checkpoint for a session

        Args:
            session_id: Session ID

        Returns:
            Path to latest checkpoint or None if no checkpoints exist
        """
        session_dir = self.checkpoint_dir / session_id
        if not session_dir.exists():
            return None

        checkpoints = list(session_dir.glob("checkpoint_*.pt"))
        if not checkpoints:
            return None

        # Sort by modification time and return the latest
        latest = max(checkpoints, key=lambda p: p.stat().st_mtime)
        return str(latest)

    def get_best_checkpoint(self, session_id: str) -> Optional[str]:
        """
        Get the path to the best checkpoint for a session

        Args:
            session_id: Session ID

        Returns:
            Path to best checkpoint or None if it doesn't exist
        """
        best_path = self.checkpoint_dir / session_id / "best_model.pt"
        if best_path.exists():
            return str(best_path)
        return None

    def list_checkpoints(self, session_id: str) -> list:
        """
        List all checkpoints for a session

        Args:
            session_id: Session ID

        Returns:
            List of checkpoint information
        """
        session_dir = self.checkpoint_dir / session_id
        if not session_dir.exists():
            return []

        checkpoints = []
        for checkpoint_path in session_dir.glob("checkpoint_*.pt"):
            try:
                # Load just the metadata
                checkpoint = torch.load(checkpoint_path, map_location=torch.device('cpu'))
                checkpoints.append({
                    "path": str(checkpoint_path),
                    "filename": checkpoint_path.name,
                    "epoch": checkpoint.get("epoch", 0),
                    "loss": checkpoint.get("loss", 0),
                    "timestamp": checkpoint.get("timestamp", ""),
                })
            except Exception:
                continue

        # Sort by epoch
        checkpoints.sort(key=lambda x: x["epoch"], reverse=True)
        return checkpoints

    def delete_checkpoint(self, checkpoint_path: str) -> bool:
        """
        Delete a checkpoint

        Args:
            checkpoint_path: Path to checkpoint to delete

        Returns:
            True if deleted successfully
        """
        try:
            path = Path(checkpoint_path)
            if path.exists():
                path.unlink()
                return True
        except Exception:
            pass
        return False

    def cleanup_old_checkpoints(self, session_id: str, keep_last: int = 5):
        """
        Clean up old checkpoints, keeping only the most recent ones

        Args:
            session_id: Session ID
            keep_last: Number of checkpoints to keep
        """
        checkpoints = self.list_checkpoints(session_id)

        # Always keep the best model
        best_path = self.get_best_checkpoint(session_id)

        # Delete older checkpoints
        for checkpoint in checkpoints[keep_last:]:
            if checkpoint["path"] != best_path:
                self.delete_checkpoint(checkpoint["path"])

    def _save_metadata(
        self,
        session_dir: Path,
        checkpoint_path: Path,
        epoch: int,
        loss: float,
        metrics: Dict[str, Any]
    ):
        """Save checkpoint metadata to JSON file"""
        metadata_path = session_dir / "checkpoints_metadata.json"

        # Load existing metadata or create new
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {"checkpoints": []}

        # Add new checkpoint info
        metadata["checkpoints"].append({
            "filename": checkpoint_path.name,
            "epoch": epoch,
            "loss": loss,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        })

        # Save updated metadata
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def export_model(
        self,
        model: nn.Module,
        export_path: str,
        model_config: Dict[str, Any],
        include_optimizer: bool = False,
        optimizer: Optional[torch.optim.Optimizer] = None
    ):
        """
        Export model for deployment or sharing

        Args:
            model: Model to export
            export_path: Path to save exported model
            model_config: Model configuration
            include_optimizer: Whether to include optimizer state
            optimizer: Optimizer (if including optimizer state)
        """
        export_data = {
            "model_state_dict": model.state_dict(),
            "model_config": model_config,
            "export_timestamp": datetime.now().isoformat()
        }

        if include_optimizer and optimizer is not None:
            export_data["optimizer_state_dict"] = optimizer.state_dict()

        torch.save(export_data, export_path)

    def load_exported_model(
        self,
        export_path: str,
        model: nn.Module
    ) -> Dict[str, Any]:
        """
        Load an exported model

        Args:
            export_path: Path to exported model
            model: Model to load state into

        Returns:
            Model configuration from export
        """
        export_data = torch.load(export_path, map_location=torch.device('cpu'))
        model.load_state_dict(export_data["model_state_dict"])
        return export_data.get("model_config", {})