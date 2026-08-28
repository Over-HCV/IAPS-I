"""Optimizer, Scheduler, and Loss function factories"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    """Focal Loss for imbalanced classification."""

    def __init__(self, alpha: torch.Tensor | None = None, gamma: float = 2.0, reduction: str = "mean"):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, inputs: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        ce_loss = F.cross_entropy(inputs, targets, weight=self.alpha, reduction="none")
        pt = torch.exp(-ce_loss)
        focal_loss = ((1 - pt) ** self.gamma) * ce_loss

        if self.reduction == "mean":
            return focal_loss.mean()
        elif self.reduction == "sum":
            return focal_loss.sum()
        return focal_loss


def create_optimizer(model: nn.Module, config: dict) -> torch.optim.Optimizer:
    """Create optimizer from training config."""
    optimizer_name = config.get("optimizer", "Adam")
    lr = config.get("learning_rate", 0.001)
    l2_decay = config.get("l2_decay", False)
    l2_lambda = config.get("l2_lambda", 0.0001) if l2_decay else 0

    if optimizer_name == "Adam":
        return torch.optim.Adam(
            model.parameters(),
            lr=lr,
            weight_decay=l2_lambda,
        )
    elif optimizer_name == "AdamW":
        return torch.optim.AdamW(
            model.parameters(),
            lr=lr,
            weight_decay=l2_lambda if l2_lambda > 0 else 0.01,
        )
    elif optimizer_name == "SGD with Momentum":
        return torch.optim.SGD(
            model.parameters(),
            lr=lr,
            momentum=0.9,
            weight_decay=l2_lambda,
        )
    elif optimizer_name == "RMSprop":
        return torch.optim.RMSprop(
            model.parameters(),
            lr=lr,
            weight_decay=l2_lambda,
        )
    else:
        raise ValueError(f"Unknown optimizer: {optimizer_name}")


def create_scheduler(
    optimizer: torch.optim.Optimizer,
    config: dict,
    steps_per_epoch: int,
) -> torch.optim.lr_scheduler.LRScheduler | None:
    """Create learning rate scheduler from training config."""
    lr_strategy = config.get("lr_strategy", "Constant")
    epochs = config.get("epochs", 100)

    if lr_strategy == "Constant":
        return None
    elif lr_strategy == "ReduceLROnPlateau":
        return torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="min",
            factor=0.5,
            patience=5,
            min_lr=1e-6,
        )
    elif lr_strategy == "Cosine Annealing":
        return torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=epochs,
            eta_min=1e-6,
        )
    elif lr_strategy == "Step Decay":
        return torch.optim.lr_scheduler.StepLR(
            optimizer,
            step_size=epochs // 3,
            gamma=0.1,
        )
    elif lr_strategy == "Exponential Decay":
        return torch.optim.lr_scheduler.ExponentialLR(
            optimizer,
            gamma=0.95,
        )
    else:
        return None


def create_criterion(
    config: dict,
    class_weights: torch.Tensor | None = None,
    device: torch.device | None = None,
) -> nn.Module:
    """Create loss function from training config."""
    class_weight_method = config.get("class_weights", "None")

    if device and class_weights is not None:
        class_weights = class_weights.to(device)

    if class_weight_method == "Focal Loss":
        return FocalLoss(alpha=class_weights, gamma=2.0)
    elif class_weight_method == "Auto Class Weights" and class_weights is not None:
        return nn.CrossEntropyLoss(weight=class_weights)
    else:
        return nn.CrossEntropyLoss()
