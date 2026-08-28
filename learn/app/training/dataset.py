"""PyTorch Dataset and DataLoader for malware images"""

from collections import Counter
from pathlib import Path

from PIL import Image
from sklearn.model_selection import train_test_split
import torch
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from training.transforms import create_train_transforms, create_val_transforms


class MalwareDataset(Dataset):
    """PyTorch Dataset for malware images."""

    def __init__(self, image_paths: list[Path], labels: list[int], transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        label = self.labels[idx]

        # Load image
        image = Image.open(img_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, label


def scan_dataset(
    dataset_path: Path, selected_families: list[str] | None = None
) -> tuple[list[Path], list[int], list[str]]:
    """Scan dataset directory and return image paths, labels, and class names."""
    image_paths = []
    labels = []
    class_names = []

    # Get all family directories
    family_dirs = sorted([d for d in dataset_path.iterdir() if d.is_dir()])

    # Filter if selected_families specified
    if selected_families:
        family_dirs = [d for d in family_dirs if d.name in selected_families]

    for class_idx, family_dir in enumerate(family_dirs):
        class_names.append(family_dir.name)
        # Get all images in this family
        for img_file in family_dir.iterdir():
            if img_file.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp"]:
                image_paths.append(img_file)
                labels.append(class_idx)

    return image_paths, labels, class_names


def create_splits(
    image_paths: list[Path],
    labels: list[int],
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    stratified: bool = True,
    random_seed: int = 72,
) -> dict:
    """Create train/val/test splits."""
    # First split: train vs (val+test)
    train_paths, temp_paths, train_labels, temp_labels = train_test_split(
        image_paths,
        labels,
        test_size=(val_ratio + test_ratio),
        random_state=random_seed,
        stratify=labels if stratified else None,
    )

    # Second split: val vs test
    val_test_ratio = test_ratio / (val_ratio + test_ratio)
    val_paths, test_paths, val_labels, test_labels = train_test_split(
        temp_paths,
        temp_labels,
        test_size=val_test_ratio,
        random_state=random_seed,
        stratify=temp_labels if stratified else None,
    )

    return {
        "train": {"paths": train_paths, "labels": train_labels},
        "val": {"paths": val_paths, "labels": val_labels},
        "test": {"paths": test_paths, "labels": test_labels},
    }


def compute_class_weights(labels: list[int], num_classes: int) -> torch.Tensor:
    """Compute inverse frequency class weights for imbalanced data."""
    counter = Counter(labels)
    total = len(labels)

    weights = []
    for i in range(num_classes):
        count = counter.get(i, 1)
        weight = total / (num_classes * count)
        weights.append(weight)

    return torch.tensor(weights, dtype=torch.float32)


def create_weighted_sampler(
    labels: list[int], num_classes: int
) -> WeightedRandomSampler:
    """Create weighted random sampler for imbalanced data."""
    class_weights = compute_class_weights(labels, num_classes)

    # Assign weight to each sample
    sample_weights = [class_weights[label].item() for label in labels]

    return WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(labels),
        replacement=True,
    )


def create_dataloaders(
    dataset_config: dict,
    training_config: dict,
    num_workers: int = 4,
) -> tuple[dict[str, DataLoader], list[str], torch.Tensor | None]:
    """
    Create DataLoaders from dataset and training configs.

    Returns:
        dataloaders: Dict with 'train', 'val', 'test' DataLoaders
        class_names: List of class names
        class_weights: Tensor of class weights (if using class weighting)
    """
    # Get dataset path
    dataset_path = Path(dataset_config.get("dataset_path", "dataset"))
    if not dataset_path.is_absolute():
        dataset_path = Path.cwd() / dataset_path

    selected_families = dataset_config.get("selected_families")

    # Scan dataset
    image_paths, labels, class_names = scan_dataset(dataset_path, selected_families)
    num_classes = len(class_names)

    print(f"[Dataset] Found {len(image_paths)} images in {num_classes} classes")

    # Get split config
    split_config = dataset_config.get("split", {})
    train_ratio = split_config.get("train", 70) / 100.0
    val_ratio = split_config.get("val", 15) / 100.0
    test_ratio = split_config.get("test", 15) / 100.0
    stratified = split_config.get("stratified", True)
    random_seed = split_config.get("random_seed", 72)

    # Create splits
    splits = create_splits(
        image_paths,
        labels,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        stratified=stratified,
        random_seed=random_seed,
    )

    print(
        f"[Dataset] Splits: train={len(splits['train']['paths'])}, val={len(splits['val']['paths'])}, test={len(splits['test']['paths'])}"
    )

    # Create transforms
    train_transform = create_train_transforms(dataset_config)
    val_transform = create_val_transforms(dataset_config)

    # Create datasets
    train_dataset = MalwareDataset(
        splits["train"]["paths"],
        splits["train"]["labels"],
        transform=train_transform,
    )
    val_dataset = MalwareDataset(
        splits["val"]["paths"],
        splits["val"]["labels"],
        transform=val_transform,
    )
    test_dataset = MalwareDataset(
        splits["test"]["paths"],
        splits["test"]["labels"],
        transform=val_transform,
    )

    # Get training config
    batch_size = training_config.get("batch_size", 32)
    class_weight_method = training_config.get("class_weights", "None")

    # Compute class weights if needed
    class_weights = None
    sampler = None

    if class_weight_method == "Auto Class Weights":
        class_weights = compute_class_weights(splits["train"]["labels"], num_classes)
        print(
            f"[Dataset] Using class weights (range: {class_weights.min():.2f} - {class_weights.max():.2f})"
        )
        # Use weighted sampler for balanced batches
        sampler = create_weighted_sampler(splits["train"]["labels"], num_classes)
    elif class_weight_method == "Focal Loss":
        class_weights = compute_class_weights(splits["train"]["labels"], num_classes)
        print(f"[Dataset] Using Focal Loss with class weights")

    # Disable pin_memory on MPS (not supported)
    import torch

    use_pin_memory = torch.cuda.is_available()

    # Create dataloaders
    dataloaders = {
        "train": DataLoader(
            train_dataset,
            batch_size=batch_size,
            sampler=sampler,
            shuffle=(sampler is None),
            num_workers=num_workers,
            pin_memory=use_pin_memory,
        ),
        "val": DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=use_pin_memory,
        ),
        "test": DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=use_pin_memory,
        ),
    }

    return dataloaders, class_names, class_weights
