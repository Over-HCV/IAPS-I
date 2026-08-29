"""
Tabular provider - one CSV row per sample

A row and an image are the same thing to the training engine: a feature tensor
and a target. The only real difference is that a row's features are built by an
encoder rather than read off disk, which is why the fitting rules below matter.
"""

from typing import Any

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

from training.dataset import create_splits
from training.providers.base import ProviderResult
from training.providers.common import class_weighting, make_loaders
from utils.dataset_registry import resolve_dataset_path
from utils.tabular_utils import build_preprocessor, fit_preprocessor, load_dataframe


class TabularDataset(Dataset):
    """Encoded feature rows with integer class labels"""

    def __init__(self, features: np.ndarray, labels: list[int]):
        self.features = torch.tensor(np.asarray(features), dtype=torch.float32)
        self.labels = labels

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int):
        return self.features[idx], self.labels[idx]


class TabularProvider:
    """Loads a CSV dataset into feature/label tensors"""

    def build_dataloaders(
        self,
        dataset_config: dict[str, Any],
        training_config: dict[str, Any],
        num_workers: int,
    ) -> ProviderResult:
        csv_path = resolve_dataset_path(dataset_config)
        if not csv_path.is_file():
            raise FileNotFoundError(f"Dataset file not found: {csv_path}")

        frame, labels, class_names = _load_labelled_rows(dataset_config, csv_path)
        num_classes = len(class_names)

        print(f"[Dataset] Found {len(frame)} rows in {num_classes} classes")

        split_config = dataset_config.get("split", {})
        row_positions = list(range(len(frame)))

        # create_splits partitions whatever indexable it is given, so the row
        # positions take the place the image paths hold in the image provider.
        splits = create_splits(
            row_positions,
            labels,
            train_ratio=split_config.get("train", 70) / 100.0,
            val_ratio=split_config.get("val", 15) / 100.0,
            test_ratio=split_config.get("test", 15) / 100.0,
            stratified=split_config.get("stratified", True),
            random_seed=split_config.get("random_seed", 72),
        )

        print(
            f"[Dataset] Splits: train={len(splits['train']['paths'])}, "
            f"val={len(splits['val']['paths'])}, test={len(splits['test']['paths'])}"
        )

        feature_columns = _feature_columns(dataset_config, frame)
        preprocessing = dataset_config.get("preprocessing", {})

        preprocessor = build_preprocessor(
            frame,
            feature_columns,
            preprocessing.get("numeric_scaling", "Standard"),
            preprocessing.get("categorical_encoding", "One-hot"),
        )
        preprocessor = fit_preprocessor(
            preprocessor,
            full_frame=frame,
            train_frame=frame.iloc[splits["train"]["paths"]],
        )

        encoded = np.asarray(preprocessor.transform(frame))

        datasets = {
            split: TabularDataset(
                encoded[splits[split]["paths"]], splits[split]["labels"]
            )
            for split in ("train", "val", "test")
        }

        class_weights, sampler = class_weighting(
            training_config, splits["train"]["labels"], num_classes
        )

        return (
            make_loaders(datasets, training_config, sampler, num_workers),
            class_names,
            class_weights,
        )


def _load_labelled_rows(
    dataset_config: dict[str, Any], csv_path
) -> tuple[pd.DataFrame, list[int], list[str]]:
    """Read the CSV, keep only the selected classes, and index the labels.

    Returns the filtered frame, integer labels aligned to it, and class names in
    the same order the label indices refer to.
    """
    target_column = dataset_config.get("target_column")
    if not target_column:
        raise ValueError("Dataset config has no target column")

    frame = load_dataframe(csv_path)
    if target_column not in frame.columns:
        raise ValueError(f"Target column '{target_column}' is not in {csv_path.name}")

    # Labels are strings everywhere so they survive the session file's JSON.
    target = frame[target_column].astype(str)

    selected = dataset_config.get("selected_families")
    class_names = sorted(selected) if selected else sorted(target.unique())

    keep = target.isin(class_names)
    frame = frame[keep].reset_index(drop=True)
    target = target[keep].reset_index(drop=True)

    if frame.empty:
        raise ValueError("No rows left after filtering to the selected classes")

    class_index = {name: index for index, name in enumerate(class_names)}
    labels = [class_index[value] for value in target]

    return frame, labels, class_names


def _feature_columns(dataset_config: dict[str, Any], frame: pd.DataFrame) -> list[str]:
    """Feature columns from the config, falling back to everything but the target"""
    target_column = dataset_config.get("target_column")
    configured = dataset_config.get("feature_columns")

    if configured:
        return [column for column in configured if column in frame.columns]

    return [column for column in frame.columns if column != target_column]
