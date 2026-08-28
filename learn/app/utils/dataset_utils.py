"""
Dataset utilities - scanning, loading, and data manipulation
"""

from pathlib import Path

from PIL import Image

from utils.dataset_registry import IMAGE_SUFFIXES


def scan_dataset(dataset_path: Path):
    """Scan one image dataset directory, treating its subfolders as classes.

    Args:
        dataset_path: Absolute path to the dataset directory

    Returns:
        dict with per-class counts, class names, total samples and preview paths
    """
    dataset_info = {
        "samples": {},
        "classes": [],
        "total_samples": 0,
        "sample_paths": {},
    }

    if not dataset_path.is_dir():
        return dataset_info

    for class_dir in sorted(dataset_path.iterdir()):
        if not class_dir.is_dir() or class_dir.name.startswith("."):
            continue

        # Same suffix set the training scanner accepts, so the counts shown in
        # the UI match the number of images actually loaded for training.
        images = sorted(
            path
            for path in class_dir.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )
        if not images:
            continue

        class_name = class_dir.name
        dataset_info["samples"][class_name] = len(images)
        dataset_info["total_samples"] += len(images)
        dataset_info["classes"].append(class_name)

        # Store sample paths for visualization
        dataset_info["sample_paths"][class_name] = images[:10]

    return dataset_info


def calculate_split_percentages(train_pct, val_of_remaining_pct):
    """
    Calculate final train/val/test percentages from 2 sliders

    Args:
        train_pct: Percentage for training (0-100)
        val_of_remaining_pct: Percentage of remaining data for validation (0-100)

    Returns:
        tuple: (train_pct, val_pct, test_pct)
    """
    remaining = 100 - train_pct
    val_pct = (remaining * val_of_remaining_pct) / 100
    test_pct = remaining - val_pct

    return train_pct, val_pct, test_pct


def get_image_dimensions(img_path):
    """Get dimensions of an image file"""
    try:
        with Image.open(img_path) as img:
            return img.size  # (width, height)
    except Exception:
        return None
