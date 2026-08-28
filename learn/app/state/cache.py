"""
Cache State Management
Temporary and cached data for expensive operations
"""

from pathlib import Path
from typing import TypedDict

import streamlit as st


class DatasetInfo(TypedDict, total=False):
    """Type definition for dataset scan cache"""

    total_train: int
    total_val: int
    classes: list[str]
    train_samples: dict[str, int]
    val_samples: dict[str, int]
    sample_paths: dict[str, list[Path]]


class CacheState(TypedDict, total=False):
    """Type definition for cache state fields"""

    dataset_info: DatasetInfo | None
    train_split: int
    val_split: int


# Default split values
DEFAULT_TRAIN_SPLIT = 70
DEFAULT_VAL_SPLIT = 50


def init_cache_state() -> None:
    """Initialize cache state with default values"""
    # dataset_info is lazy-loaded, not initialized here
    # train_split and val_split are Streamlit widget keys, auto-initialized

    if "train_split" not in st.session_state:
        st.session_state.train_split = DEFAULT_TRAIN_SPLIT

    if "val_split" not in st.session_state:
        st.session_state.val_split = DEFAULT_VAL_SPLIT


# Dataset Info Cache
def get_dataset_info() -> DatasetInfo | None:
    """Get cached dataset scan information"""
    return st.session_state.get("dataset_info")


def set_dataset_info(info: DatasetInfo) -> None:
    """Cache dataset scan information"""
    st.session_state.dataset_info = info


def has_dataset_info() -> bool:
    """Check if dataset info is cached"""
    return (
        "dataset_info" in st.session_state and st.session_state.dataset_info is not None
    )


def clear_dataset_info() -> None:
    """Clear cached dataset information"""
    if "dataset_info" in st.session_state:
        del st.session_state.dataset_info


# Dataset Split Configuration
def get_train_split() -> int:
    """Get training split percentage"""
    return st.session_state.get("train_split", DEFAULT_TRAIN_SPLIT)


def set_train_split(split: int) -> None:
    """Set training split percentage"""
    st.session_state.train_split = split


def get_val_split() -> int:
    """Get validation split percentage"""
    return st.session_state.get("val_split", DEFAULT_VAL_SPLIT)


def set_val_split(split: int) -> None:
    """Set validation split percentage"""
    st.session_state.val_split = split


def get_splits() -> tuple[int, int]:
    """Get both train and validation splits as tuple"""
    return (get_train_split(), get_val_split())


def set_splits(train: int, val: int) -> None:
    """Set both train and validation splits"""
    st.session_state.train_split = train
    st.session_state.val_split = val


def reset_splits_to_defaults() -> None:
    """Reset split values to defaults"""
    set_splits(DEFAULT_TRAIN_SPLIT, DEFAULT_VAL_SPLIT)


def clear_cache_state() -> None:
    """Clear all cached data"""
    keys_to_clear = [
        "dataset_info",
        "train_split",
        "val_split",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    # Reinitialize splits
    init_cache_state()
