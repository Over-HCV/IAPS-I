"""
Workflow State Management
Core ML workflow configuration and session state
"""

from datetime import datetime
import random
from typing import Any, TypedDict
import uuid

import streamlit as st

# Bird-only word lists for combinatoric session names
_ADJECTIVES = [
    "swift", "gentle", "bold", "quiet", "bright", "calm", "wild", "keen",
    "proud", "noble", "agile", "clever", "silent", "graceful", "fierce",
]
_TONES = [
    "golden", "silver", "azure", "crimson", "emerald", "amber", "ivory",
    "dusky", "misty", "sunny", "stormy", "frosty", "coastal", "alpine",
]
_BIRDS = [
    "sparrow", "falcon", "eagle", "hawk", "owl", "raven", "crow", "robin",
    "finch", "wren", "jay", "cardinal", "swan", "dove",
    "lark", "thrush", "oriole", "tanager", "warbler", "kingfisher",
    "kestrel", "merlin", "harrier", "condor", "pelican", "stork",
    "ibis", "flamingo", "toucan", "parrot", "macaw", "cockatoo",
    "parakeet", "hummingbird", "woodpecker", "magpie", "starling", "swallow",
    "albatross", "puffin", "penguin", "cormorant", "tern", "seagull", "plover",
]


class WorkflowState(TypedDict, total=False):
    """Type definition for workflow state fields"""

    session_id: str
    dataset_config: dict[str, Any]

    # Libraries (multiple saved configs)
    model_library: list[dict[str, Any]]
    training_library: list[dict[str, Any]]

    # Experiments (model + training combinations)
    experiments: list[dict[str, Any]]

    # Legacy (kept for backwards compatibility)
    model_config: dict[str, Any]
    training_config: dict[str, Any]
    training_active: bool
    monitor_config: dict[str, Any]
    results: dict[str, Any] | None


def init_workflow_state() -> None:
    """Initialize workflow state with default values.

    On startup, checks for a persisted session ID and loads it if available.
    This ensures the selected session survives page reloads.
    """
    if "session_id" not in st.session_state:
        # Check for persisted session first
        from state.persistence import get_persisted_session_id, load_session

        persisted_id = get_persisted_session_id()
        if persisted_id:
            # Try to load the persisted session
            if load_session(persisted_id):
                return  # Session loaded, don't initialize defaults

        # No persisted session or load failed - create new session with bird name
        st.session_state.session_id = generate_session_id()

    if "dataset_config" not in st.session_state:
        st.session_state.dataset_config = {}

    # Libraries
    if "model_library" not in st.session_state:
        st.session_state.model_library = []

    if "training_library" not in st.session_state:
        st.session_state.training_library = []

    # Experiments
    if "experiments" not in st.session_state:
        st.session_state.experiments = []

    # Legacy (backwards compatibility)
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


def generate_session_id() -> str:
    """Generate bird-based session ID like 'swift-golden-falcon'"""
    adj1 = random.choice(_ADJECTIVES)
    adj2 = random.choice(_TONES)
    bird = random.choice(_BIRDS)
    return f"{adj1}-{adj2}-{bird}"


# Session ID
def get_session_id() -> str:
    """Get current session ID (bird-based name)"""
    return st.session_state.get("session_id", "")


# Dataset Configuration
def save_dataset_config(config: dict[str, Any]) -> None:
    """Save dataset configuration to session state and persist to disk"""
    st.session_state.dataset_config = config

    # Auto-save session to disk
    from state.persistence import save_session

    session_id = get_session_id()
    if session_id:
        save_session(session_id)


def get_dataset_config() -> dict[str, Any]:
    """Retrieve dataset configuration"""
    return st.session_state.get("dataset_config", {})


def has_dataset_config() -> bool:
    """Check if dataset is configured"""
    return bool(st.session_state.get("dataset_config"))


# Model Configuration
def save_model_config(config: dict[str, Any]) -> None:
    """Save model configuration to session state and persist to disk"""
    st.session_state.model_config = config

    # Auto-save session to disk
    from state.persistence import save_session

    session_id = get_session_id()
    if session_id:
        save_session(session_id)


def get_model_config() -> dict[str, Any]:
    """Retrieve model configuration"""
    return st.session_state.get("model_config", {})


def has_model_config() -> bool:
    """Check if model is configured"""
    return bool(st.session_state.get("model_config"))


# Training Configuration
def save_training_config(config: dict[str, Any]) -> None:
    """Save training configuration to session state and persist to disk"""
    st.session_state.training_config = config

    # Auto-save session to disk
    from state.persistence import save_session

    session_id = get_session_id()
    if session_id:
        save_session(session_id)


def get_training_config() -> dict[str, Any]:
    """Retrieve training configuration"""
    return st.session_state.get("training_config", {})


def has_training_config() -> bool:
    """Check if training is configured"""
    return bool(st.session_state.get("training_config"))


def has_models_in_library() -> bool:
    """Check if at least one model exists in library"""
    return len(st.session_state.get("model_library", [])) > 0


def has_completed_training() -> bool:
    """Check if at least one experiment has completed"""
    experiments = st.session_state.get("experiments", [])
    return any(exp.get("status") == "completed" for exp in experiments)


# Training Status
def is_training_active() -> bool:
    """Check if training is currently active"""
    return st.session_state.get("training_active", False)


def set_training_active(active: bool) -> None:
    """Set training active status"""
    st.session_state.training_active = active


# Results
def save_results(results: dict[str, Any]) -> None:
    """Save training results to session state and persist to disk"""
    st.session_state.results = results

    # Auto-save session to disk
    from state.persistence import save_session

    session_id = get_session_id()
    if session_id:
        save_session(session_id)


def get_results() -> dict[str, Any] | None:
    """Retrieve training results"""
    return st.session_state.get("results")


def has_results() -> bool:
    """Check if results are available"""
    return st.session_state.get("results") is not None


# =============================================================================
# Model Library CRUD
# =============================================================================


def _auto_save() -> None:
    """Auto-save session to disk and persist session ID"""
    from state.persistence import save_session, set_persisted_session_id

    session_id = get_session_id()
    if session_id:
        save_session(session_id)
        set_persisted_session_id(session_id)


def add_model_to_library(name: str, config: dict[str, Any]) -> str:
    """Add a new model to the library. Returns the model ID."""
    model_id = f"model_{uuid.uuid4().hex[:8]}"
    model_entry = {
        "id": model_id,
        "name": name,
        "model_type": config.get("model_type", "Unknown"),
        "created_at": datetime.now().isoformat(),
        "config": config,
    }
    st.session_state.model_library.append(model_entry)
    _auto_save()
    return model_id


def get_model_from_library(model_id: str) -> dict[str, Any] | None:
    """Get a model by ID from the library"""
    for model in st.session_state.get("model_library", []):
        if model["id"] == model_id:
            return model
    return None


def update_model_in_library(model_id: str, name: str, config: dict[str, Any]) -> bool:
    """Update an existing model in the library. Returns True if found."""
    for model in st.session_state.get("model_library", []):
        if model["id"] == model_id:
            model["name"] = name
            model["model_type"] = config.get("model_type", "Unknown")
            model["config"] = config
            _auto_save()
            return True
    return False


def delete_model_from_library(model_id: str) -> bool:
    """Delete a model from the library. Returns True if found."""
    library = st.session_state.get("model_library", [])
    for i, model in enumerate(library):
        if model["id"] == model_id:
            library.pop(i)
            _auto_save()
            return True
    return False


def get_model_library() -> list[dict[str, Any]]:
    """Get all models in the library"""
    return st.session_state.get("model_library", [])


# =============================================================================
# Training Library CRUD
# =============================================================================


def add_training_to_library(name: str, config: dict[str, Any]) -> str:
    """Add a new training config to the library. Returns the training ID."""
    training_id = f"train_{uuid.uuid4().hex[:8]}"
    training_entry = {
        "id": training_id,
        "name": name,
        "created_at": datetime.now().isoformat(),
        "config": config,
    }
    st.session_state.training_library.append(training_entry)
    _auto_save()
    return training_id


def get_training_from_library(training_id: str) -> dict[str, Any] | None:
    """Get a training config by ID from the library"""
    for training in st.session_state.get("training_library", []):
        if training["id"] == training_id:
            return training
    return None


def update_training_in_library(
    training_id: str, name: str, config: dict[str, Any]
) -> bool:
    """Update an existing training config in the library. Returns True if found."""
    for training in st.session_state.get("training_library", []):
        if training["id"] == training_id:
            training["name"] = name
            training["config"] = config
            _auto_save()
            return True
    return False


def delete_training_from_library(training_id: str) -> bool:
    """Delete a training config from the library. Returns True if found."""
    library = st.session_state.get("training_library", [])
    for i, training in enumerate(library):
        if training["id"] == training_id:
            library.pop(i)
            _auto_save()
            return True
    return False


def get_training_library() -> list[dict[str, Any]]:
    """Get all training configs in the library"""
    return st.session_state.get("training_library", [])


# =============================================================================
# Experiments CRUD
# =============================================================================


def create_experiment(name: str, model_id: str, training_id: str) -> str:
    """Create a new experiment. Returns the experiment ID."""
    exp_id = f"exp_{uuid.uuid4().hex[:8]}"
    experiment = {
        "id": exp_id,
        "name": name,
        "model_id": model_id,
        "training_id": training_id,
        "status": "ready",  # ready, training, paused, completed, failed
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "current_epoch": 0,
        "metrics": {},
        "results_id": None,
    }
    st.session_state.experiments.append(experiment)
    _auto_save()
    return exp_id


def get_experiment(exp_id: str) -> dict[str, Any] | None:
    """Get an experiment by ID"""
    for exp in st.session_state.get("experiments", []):
        if exp["id"] == exp_id:
            return exp
    return None


def update_experiment(exp_id: str, updates: dict[str, Any]) -> bool:
    """Update experiment fields. Returns True if found."""
    for exp in st.session_state.get("experiments", []):
        if exp["id"] == exp_id:
            exp.update(updates)
            _auto_save()
            return True
    return False


def delete_experiment(exp_id: str) -> bool:
    """Delete an experiment. Returns True if found."""
    experiments = st.session_state.get("experiments", [])
    for i, exp in enumerate(experiments):
        if exp["id"] == exp_id:
            experiments.pop(i)
            _auto_save()
            return True
    return False


def get_experiments() -> list[dict[str, Any]]:
    """Get all experiments"""
    return st.session_state.get("experiments", [])


# =============================================================================
# Session Management
# =============================================================================


def clear_workflow_state() -> None:
    """Clear workflow-related session state"""
    keys_to_clear = [
        "session_id",
        "dataset_config",
        "model_library",
        "training_library",
        "experiments",
        "model_config",
        "training_config",
        "training_active",
        "monitor_config",
        "results",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    # Reinitialize with fresh values
    init_workflow_state()
