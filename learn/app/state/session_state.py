"""
Session State Management
BFS Level: Interface definitions only
"""

from datetime import datetime
from typing import Any

import streamlit as st


def init_session_state():
    """Initialize session state with default values"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = generate_session_id()

    if "dataset_config" not in st.session_state:
        st.session_state.dataset_config = {}

    if "model_config" not in st.session_state:
        st.session_state.model_config = {}

    if "training_config" not in st.session_state:
        st.session_state.training_config = {}

    if "training_active" not in st.session_state:
        st.session_state.training_active = False

    if "monitor_config" not in st.session_state:
        st.session_state.monitor_config = {}

    if "results" not in st.session_state:
        st.session_state.results = None

    # Sensible defaults for dataset configuration
    if "train_split" not in st.session_state:
        st.session_state.train_split = 70

    if "val_split" not in st.session_state:
        st.session_state.val_split = 50  # 50% of remaining = 15% total

    if "stratified_split" not in st.session_state:
        st.session_state.stratified_split = True

    if "random_seed" not in st.session_state:
        st.session_state.random_seed = 73

    if "imbalance_strategy" not in st.session_state:
        st.session_state.imbalance_strategy = "Auto Class Weights (Recommended)"

    if "augmentation_preset" not in st.session_state:
        st.session_state.augmentation_preset = "Custom"

    # Custom augmentation defaults
    if "aug_v_flip" not in st.session_state:
        st.session_state.aug_v_flip = True

    # Selective augmentation defaults (for H2 hypothesis)
    if "minority_threshold" not in st.session_state:
        st.session_state.minority_threshold = 200

    if "aug_multiplier" not in st.session_state:
        st.session_state.aug_multiplier = 2.0


def generate_session_id() -> str:
    """Generate unique session ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"session_{timestamp}"


def save_dataset_config(config: dict[str, Any]):
    """Save dataset configuration to session state"""
    st.session_state.dataset_config = config


def save_model_config(config: dict[str, Any]):
    """Save model configuration to session state"""
    st.session_state.model_config = config


def save_training_config(config: dict[str, Any]):
    """Save training configuration to session state"""
    st.session_state.training_config = config


def get_dataset_config() -> dict[str, Any]:
    """Retrieve dataset configuration"""
    return st.session_state.get("dataset_config", {})


def get_model_config() -> dict[str, Any]:
    """Retrieve model configuration"""
    return st.session_state.get("model_config", {})


def get_training_config() -> dict[str, Any]:
    """Retrieve training configuration"""
    return st.session_state.get("training_config", {})


def is_training_active() -> bool:
    """Check if training is currently active"""
    return st.session_state.get("training_active", False)


def set_training_active(active: bool):
    """Set training active status"""
    st.session_state.training_active = active


def save_results(results: dict[str, Any]):
    """Save training results to session state"""
    st.session_state.results = results


def get_results() -> dict[str, Any] | None:
    """Retrieve training results"""
    return st.session_state.get("results")


def clear_session():
    """Clear all session state"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()
