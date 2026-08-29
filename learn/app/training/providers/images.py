"""
Image folder provider - one subfolder per class, images inside

This is the original dataset pipeline, moved behind the provider boundary
unchanged in behaviour.
"""

from typing import Any

from training.dataset import ImageSampleDataset, create_splits, scan_dataset
from training.providers.base import ProviderResult
from training.providers.common import class_weighting, make_loaders
from training.transforms import create_train_transforms, create_val_transforms
from utils.dataset_registry import resolve_dataset_path


class ImageFolderProvider:
    """Loads image datasets laid out as <dataset>/<class>/*.png"""

    def build_dataloaders(
        self,
        dataset_config: dict[str, Any],
        training_config: dict[str, Any],
        num_workers: int,
    ) -> ProviderResult:
        dataset_path = resolve_dataset_path(dataset_config)
        if not dataset_path.is_dir():
            raise FileNotFoundError(f"Dataset directory not found: {dataset_path}")

        selected_families = dataset_config.get("selected_families")

        image_paths, labels, class_names = scan_dataset(dataset_path, selected_families)
        num_classes = len(class_names)

        print(f"[Dataset] Found {len(image_paths)} images in {num_classes} classes")

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

        print(
            f"[Dataset] Splits: train={len(splits['train']['paths'])}, "
            f"val={len(splits['val']['paths'])}, test={len(splits['test']['paths'])}"
        )

        train_transform = create_train_transforms(dataset_config)
        val_transform = create_val_transforms(dataset_config)

        datasets = {
            "train": ImageSampleDataset(
                splits["train"]["paths"], splits["train"]["labels"], train_transform
            ),
            "val": ImageSampleDataset(
                splits["val"]["paths"], splits["val"]["labels"], val_transform
            ),
            "test": ImageSampleDataset(
                splits["test"]["paths"], splits["test"]["labels"], val_transform
            ),
        }

        class_weights, sampler = class_weighting(
            training_config, splits["train"]["labels"], num_classes
        )

        return (
            make_loaders(datasets, training_config, sampler, num_workers),
            class_names,
            class_weights,
        )
