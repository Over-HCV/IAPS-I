"""Training Engine - Core training loop"""

import time
from typing import Callable

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score
import torch
import torch.nn as nn
from torch.utils.data import DataLoader


class TrainingEngine:
    """Handles the training loop with callbacks and early stopping."""

    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        optimizer: torch.optim.Optimizer,
        criterion: nn.Module,
        device: torch.device,
        scheduler: torch.optim.lr_scheduler.LRScheduler | None = None,
        early_stopping_patience: int = 0,
        checkpoint_callback: Callable | None = None,
        batch_callback: Callable[[int, int, dict], None] | None = None,
    ):
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.optimizer = optimizer
        self.criterion = criterion
        self.device = device
        self.scheduler = scheduler
        self.early_stopping_patience = early_stopping_patience
        self.checkpoint_callback = checkpoint_callback
        self.batch_callback = batch_callback

        # Training state
        self.current_epoch = 0
        self.best_val_loss = float("inf")
        self.best_epoch = 0
        self.epochs_without_improvement = 0
        self.should_stop = False
        self.is_paused = False

        # History - tracks all metrics per epoch
        self.history = {
            "train_loss": [],
            "train_acc": [],
            "train_precision": [],
            "train_recall": [],
            "train_f1": [],
            "val_loss": [],
            "val_acc": [],
            "val_precision": [],
            "val_recall": [],
            "val_f1": [],
            "lr": [],
        }

    def train_epoch(self) -> dict:
        """Train for one epoch."""
        self.model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        total_batches = len(self.train_loader)

        # Collect predictions for precision/recall/F1
        all_preds = []
        all_targets = []

        for batch_idx, (inputs, targets) in enumerate(self.train_loader):
            inputs, targets = inputs.to(self.device), targets.to(self.device)

            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(inputs)
            loss = self.criterion(outputs, targets)

            # Backward pass
            loss.backward()
            self.optimizer.step()

            # Statistics
            running_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()

            # Collect for metrics calculation
            all_preds.extend(predicted.cpu().numpy())
            all_targets.extend(targets.cpu().numpy())

            # Report batch progress every 10 batches
            if self.batch_callback and (batch_idx + 1) % 10 == 0:
                self.batch_callback(
                    batch_idx + 1,
                    total_batches,
                    {
                        "batch_loss": running_loss / total,
                        "batch_acc": correct / total,
                    },
                )

            # Check for stop signal
            if self.should_stop:
                break

        avg_loss = running_loss / total
        accuracy = correct / total

        # Compute precision, recall, F1 (macro average)
        all_preds = np.array(all_preds)
        all_targets = np.array(all_targets)
        precision = precision_score(
            all_targets, all_preds, average="macro", zero_division=0
        )
        recall = recall_score(all_targets, all_preds, average="macro", zero_division=0)
        f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)

        return {
            "train_loss": avg_loss,
            "train_acc": accuracy,
            "train_precision": precision,
            "train_recall": recall,
            "train_f1": f1,
        }

    @torch.no_grad()
    def validate(self) -> dict:
        """Validate the model."""
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0

        # Collect predictions for precision/recall/F1
        all_preds = []
        all_targets = []

        for inputs, targets in self.val_loader:
            inputs, targets = inputs.to(self.device), targets.to(self.device)

            outputs = self.model(inputs)
            loss = self.criterion(outputs, targets)

            running_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()

            # Collect for metrics calculation
            all_preds.extend(predicted.cpu().numpy())
            all_targets.extend(targets.cpu().numpy())

        avg_loss = running_loss / total
        accuracy = correct / total

        # Compute precision, recall, F1 (macro average)
        all_preds = np.array(all_preds)
        all_targets = np.array(all_targets)
        precision = precision_score(
            all_targets, all_preds, average="macro", zero_division=0
        )
        recall = recall_score(all_targets, all_preds, average="macro", zero_division=0)
        f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)

        return {
            "val_loss": avg_loss,
            "val_acc": accuracy,
            "val_precision": precision,
            "val_recall": recall,
            "val_f1": f1,
        }

    def fit(
        self,
        epochs: int,
        update_callback: Callable[[int, dict], None] | None = None,
    ) -> dict:
        """
        Run the full training loop.

        Args:
            epochs: Number of epochs to train
            update_callback: Called after each epoch with (epoch, metrics)

        Returns:
            Final metrics dict
        """
        start_time = time.time()
        print(f"\n{'=' * 60}")
        print(f"Starting training for {epochs} epochs")
        print(f"Device: {self.device}")
        print(
            f"Train batches: {len(self.train_loader)}, Val batches: {len(self.val_loader)}"
        )
        print(f"{'=' * 60}\n")

        for epoch in range(epochs):
            if self.should_stop:
                print(f"\n[Epoch {epoch + 1}] Training stopped by user")
                break

            # Wait if paused
            while self.is_paused and not self.should_stop:
                time.sleep(0.5)

            self.current_epoch = epoch + 1
            epoch_start = time.time()

            # Train
            train_metrics = self.train_epoch()

            # Validate
            val_metrics = self.validate()

            # Combine metrics
            metrics = {**train_metrics, **val_metrics}
            current_lr = self.optimizer.param_groups[0]["lr"]
            metrics["lr"] = current_lr

            # Update history
            for key, value in metrics.items():
                if key in self.history:
                    self.history[key].append(value)

            # Scheduler step
            if self.scheduler:
                if isinstance(
                    self.scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau
                ):
                    self.scheduler.step(val_metrics["val_loss"])
                else:
                    self.scheduler.step()

            # Check for best model
            is_best = val_metrics["val_loss"] < self.best_val_loss
            if is_best:
                self.best_val_loss = val_metrics["val_loss"]
                self.best_epoch = epoch + 1
                self.epochs_without_improvement = 0
            else:
                self.epochs_without_improvement += 1

            # Checkpoint callback
            if self.checkpoint_callback:
                self.checkpoint_callback(epoch + 1, metrics, is_best)

            # Print progress
            epoch_time = time.time() - epoch_start
            print(
                f"Epoch {epoch + 1:3d}/{epochs} | "
                f"Train Loss: {train_metrics['train_loss']:.4f} | "
                f"Train Acc: {train_metrics['train_acc'] * 100:.1f}% | "
                f"Val Loss: {val_metrics['val_loss']:.4f} | "
                f"Val Acc: {val_metrics['val_acc'] * 100:.1f}% | "
                f"LR: {current_lr:.6f} | "
                f"Time: {epoch_time:.1f}s" + (" *" if is_best else "")
            )

            # Update callback
            if update_callback:
                update_callback(epoch + 1, metrics)

            # Early stopping check
            if self.early_stopping_patience > 0:
                if self.epochs_without_improvement >= self.early_stopping_patience:
                    print(
                        f"\nEarly stopping triggered after {epoch + 1} epochs (patience: {self.early_stopping_patience})"
                    )
                    break

        # Training complete
        total_time = time.time() - start_time
        minutes = int(total_time // 60)
        seconds = int(total_time % 60)

        print(f"\n{'=' * 60}")
        print(f"Training completed in {minutes}m {seconds}s")
        print(f"Best epoch: {self.best_epoch} with val_loss: {self.best_val_loss:.4f}")
        print(f"{'=' * 60}\n")

        return {
            "final_epoch": self.current_epoch,
            "best_epoch": self.best_epoch,
            "best_val_loss": self.best_val_loss,
            "duration": f"{minutes}m {seconds}s",
            "history": self.history,
        }

    def stop(self):
        """Signal to stop training."""
        self.should_stop = True

    def pause(self):
        """Pause training."""
        self.is_paused = True

    def resume(self):
        """Resume training."""
        self.is_paused = False
