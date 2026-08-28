"""Data loading utilities for interpretability."""

from pathlib import Path

from state.persistence import get_dataset_config_from_file
from state.workflow import get_session_id
from training.dataset import create_dataloaders, create_splits, scan_dataset


def get_test_dataloader(batch_size: int = 32, num_workers: int = 2):
    """
    Get test dataloader for current session.

    Returns:
        Tuple of (test_loader, class_names)
    """
    session_id = get_session_id()
    dataset_config = get_dataset_config_from_file(session_id)

    if not dataset_config:
        raise ValueError("No dataset configuration found")

    dataloaders, class_names, _ = create_dataloaders(
        dataset_config,
        {"batch_size": batch_size},
        num_workers=num_workers,
    )

    return dataloaders["test"], class_names


def get_test_samples(n_samples: int = 10) -> list[dict]:
    """
    Get a batch of test samples with their paths and labels.

    Returns:
        List of dicts with 'path', 'label', 'class_name'
    """
    session_id = get_session_id()
    dataset_config = get_dataset_config_from_file(session_id)

    if not dataset_config:
        return []

    dataset_path = Path(dataset_config.get("dataset_path", "dataset"))
    if not dataset_path.is_absolute():
        dataset_path = Path.cwd() / dataset_path

    selected_families = dataset_config.get("selected_families")
    image_paths, labels, class_names = scan_dataset(dataset_path, selected_families)

    split_config = dataset_config.get("split", {})
    splits = create_splits(
        image_paths,
        labels,
        train_ratio=split_config.get("train", 70) / 100.0,
        val_ratio=split_config.get("val", 15) / 100.0,
        test_ratio=split_config.get("test", 15) / 100.0,
        stratified=split_config.get("stratified", True),
        random_seed=split_config.get("random_seed", 72),
    )

    test_paths = splits["test"]["paths"]
    test_labels = splits["test"]["labels"]

    samples = []
    for i, (path, label) in enumerate(
        zip(test_paths[:n_samples], test_labels[:n_samples], strict=False)
    ):
        samples.append({
            "index": i,
            "path": str(path),
            "label": label,
            "class_name": class_names[label],
        })

    return samples
