"""
Data provider protocol

A provider turns a saved dataset config into the tuple the training worker and
the evaluator already expect. Everything specific to one kind of data - how a
sample is read off disk, how features are built - lives behind this boundary, so
the training engine never learns what an input actually is.
"""

from typing import Any, Protocol

import torch
from torch.utils.data import DataLoader

# The tuple every provider returns: dataloaders by split, class names, and
# optional class weights for imbalance handling.
ProviderResult = tuple[dict[str, DataLoader], list[str], torch.Tensor | None]


class DataProvider(Protocol):
    """Builds dataloaders for one kind of dataset"""

    def build_dataloaders(
        self,
        dataset_config: dict[str, Any],
        training_config: dict[str, Any],
        num_workers: int,
    ) -> ProviderResult:
        """Create train/val/test DataLoaders from a saved dataset config"""
        ...
