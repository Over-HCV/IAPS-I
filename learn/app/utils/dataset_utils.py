"""
Dataset utilities - scanning, loading, and data manipulation
"""

from pathlib import Path

from PIL import Image

# Dataset paths relative to project root
DATASET_ROOT = Path(__file__).parent.parent.parent / "dataset"


def scan_dataset():
    """Scan dataset directory"""
    dataset_info = {
        "samples": {},
        "classes": [],
        "total_samples": 0,
        "sample_paths": {},
    }

    # Scan dataset directory
    if DATASET_ROOT.exists():
        for class_dir in sorted(DATASET_ROOT.iterdir()):
            if class_dir.is_dir() and not class_dir.name.startswith('.'):
                images = list(class_dir.glob("*.png"))
                class_name = class_dir.name
                
                if images:
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
    except:
        return None
