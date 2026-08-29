"""
Pieces shared by every data provider

Batching and class weighting depend on the labels and the training config, not
on what a sample is, so both providers use the same implementation.
"""

from typing import Any

import torch
from torch.utils.data import DataLoader, Dataset

from training.dataset import compute_class_weights, create_weighted_sampler


def class_weighting(
    training_config: dict[str, Any], train_labels: list[int], num_classes: int
) -> tuple[torch.Tensor | None, Any]:
    """Compute class weights and a balancing sampler when requested.

    Returns (weights, sampler); either may be None.
    """
    method = training_config.get("class_weights", "None")

    if method == "Auto Class Weights":
        weights = compute_class_weights(train_labels, num_classes)
        print(
            f"[Dataset] Using class weights "
            f"(range: {weights.min():.2f} - {weights.max():.2f})"
        )
        return weights, create_weighted_sampler(train_labels, num_classes)

    if method == "Focal Loss":
        print("[Dataset] Using Focal Loss with class weights")
        return compute_class_weights(train_labels, num_classes), None

    return None, None


def make_loaders(
    datasets: dict[str, Dataset],
    training_config: dict[str, Any],
    sampler: Any = None,
    num_workers: int = 4,
) -> dict[str, DataLoader]:
    """Wrap train/val/test datasets in DataLoaders.

    The sampler applies to the training split only; validation and test are read
    in a fixed order so their metrics are comparable across epochs.
    """
    batch_size = training_config.get("batch_size", 32)

    # pin_memory is a CUDA feature and is not supported on MPS
    use_pin_memory = torch.cuda.is_available()

    loaders = {
        "train": DataLoader(
            datasets["train"],
            batch_size=batch_size,
            sampler=sampler,
            shuffle=(sampler is None),
            num_workers=num_workers,
            pin_memory=use_pin_memory,
        )
    }

    for split in ("val", "test"):
        loaders[split] = DataLoader(
            datasets[split],
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=use_pin_memory,
        )

    return loaders
