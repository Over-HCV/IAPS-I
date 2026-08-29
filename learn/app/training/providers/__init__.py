"""
Provider registry - maps a dataset kind to the code that loads it
"""

from typing import Any

from training.providers.base import ProviderResult
from training.providers.images import ImageFolderProvider
from training.providers.tabular import TabularProvider

IMAGE_FOLDER = "image_folder"
TABULAR = "tabular"

# Configs saved before data kinds existed have no marker and are always images.
DEFAULT_KIND = IMAGE_FOLDER

_PROVIDERS = {
    IMAGE_FOLDER: ImageFolderProvider(),
    TABULAR: TabularProvider(),
}


def get_dataset_kind(dataset_config: dict[str, Any]) -> str:
    """Read the data kind from a dataset config, defaulting to images"""
    return dataset_config.get("dataset_kind", DEFAULT_KIND)


def get_provider(kind: str):
    """Look up the provider for a dataset kind"""
    provider = _PROVIDERS.get(kind)
    if provider is None:
        raise ValueError(
            f"Unknown dataset kind '{kind}'. Known kinds: {sorted(_PROVIDERS)}"
        )

    return provider


def build_dataloaders(
    dataset_config: dict[str, Any],
    training_config: dict[str, Any],
    num_workers: int = 4,
) -> ProviderResult:
    """Dispatch to the provider matching the config's dataset kind"""
    provider = get_provider(get_dataset_kind(dataset_config))

    return provider.build_dataloaders(dataset_config, training_config, num_workers)
