"""
Session Persistence
Save and load training sessions to/from disk
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any

import streamlit as st

# Sessions storage directory
SESSIONS_DIR = Path(__file__).parent.parent.parent / "sessions"


def get_sessions_directory() -> Path:
    """Get the sessions storage directory, creating it if needed"""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return SESSIONS_DIR


def save_session(session_id: str) -> bool:
    """
    Save current session state to disk

    Args:
        session_id: Session identifier to save

    Returns:
        True if saved successfully, False otherwise
    """
    try:
        sessions_dir = get_sessions_directory()
        filepath = sessions_dir / f"{session_id}.json"

        # Gather workflow state
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "dataset_config": st.session_state.get("dataset_config", {}),
            # Libraries
            "model_library": st.session_state.get("model_library", []),
            "training_library": st.session_state.get("training_library", []),
            # Experiments
            "experiments": st.session_state.get("experiments", []),
            # Legacy (backwards compatibility)
            "model_config": st.session_state.get("model_config", {}),
            "training_config": st.session_state.get("training_config", {}),
            "training_active": st.session_state.get("training_active", False),
            "monitor_config": st.session_state.get("monitor_config", {}),
            "results": st.session_state.get("results"),
        }

        # Write to file
        with open(filepath, "w") as f:
            json.dump(session_data, f, indent=2)

        return True

    except Exception as e:
        st.error(f"Failed to save session: {e}")
        return False


def load_session(session_id: str) -> bool:
    """
    Load session state from disk into st.session_state

    Args:
        session_id: Session identifier to load

    Returns:
        True if loaded successfully, False otherwise
    """
    try:
        sessions_dir = get_sessions_directory()
        filepath = sessions_dir / f"{session_id}.json"

        if not filepath.exists():
            st.error(f"Session file not found: {session_id}")
            return False

        # Read from file
        with open(filepath) as f:
            session_data = json.load(f)

        # Restore workflow state
        st.session_state.session_id = session_data.get("session_id", session_id)
        st.session_state.dataset_config = session_data.get("dataset_config", {})
        # Libraries
        st.session_state.model_library = session_data.get("model_library", [])
        st.session_state.training_library = session_data.get("training_library", [])
        # Experiments
        st.session_state.experiments = session_data.get("experiments", [])
        # Legacy (backwards compatibility)
        st.session_state.model_config = session_data.get("model_config", {})
        st.session_state.training_config = session_data.get("training_config", {})
        st.session_state.training_active = session_data.get("training_active", False)
        st.session_state.monitor_config = session_data.get("monitor_config", {})
        st.session_state.results = session_data.get("results")

        return True

    except Exception as e:
        st.error(f"Failed to load session: {e}")
        return False


def list_saved_sessions() -> list[str]:
    """
    Get list of all saved session IDs

    Returns:
        List of session IDs sorted by modification time (newest first)
    """
    try:
        sessions_dir = get_sessions_directory()

        # Find all .json files
        session_files = list(sessions_dir.glob("*.json"))

        # Sort by modification time (newest first)
        session_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Extract session IDs (filename without .json)
        session_ids = [f.stem for f in session_files]

        return session_ids

    except Exception as e:
        st.error(f"Failed to list sessions: {e}")
        return []


def delete_session(session_id: str) -> bool:
    """
    Delete a saved session file

    Args:
        session_id: Session identifier to delete

    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        sessions_dir = get_sessions_directory()
        filepath = sessions_dir / f"{session_id}.json"

        if filepath.exists():
            filepath.unlink()
            return True
        else:
            st.warning(f"Session file not found: {session_id}")
            return False

    except Exception as e:
        st.error(f"Failed to delete session: {e}")
        return False


def get_session_metadata(session_id: str) -> dict[str, Any] | None:
    """
    Get metadata for a session without loading full state

    Args:
        session_id: Session identifier

    Returns:
        Dictionary with metadata or None if not found
    """
    try:
        sessions_dir = get_sessions_directory()
        filepath = sessions_dir / f"{session_id}.json"

        if not filepath.exists():
            return None

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        return {
            "session_id": data.get("session_id"),
            "created_at": data.get("created_at"),
            "has_dataset": bool(data.get("dataset_config")),
            "model_count": len(data.get("model_library", [])),
            "training_count": len(data.get("training_library", [])),
            "experiment_count": len(data.get("experiments", [])),
            # Legacy
            "has_model": bool(data.get("model_config")),
            "has_training": bool(data.get("training_config")),
            "has_results": data.get("results") is not None,
        }

    except Exception as exception:
        st.error(f"Failed to get session metadata: {exception}")
        return None


# =============================================================================
# Thread-safe File I/O (for background training threads)
# =============================================================================

import threading

_file_lock = threading.Lock()


def read_session_data(session_id: str) -> dict[str, Any] | None:
    """
    Read session data directly from JSON file.
    Thread-safe - can be called from background threads.

    Args:
        session_id: Session identifier

    Returns:
        Session data dict or None if not found
    """
    try:
        sessions_dir = get_sessions_directory()
        filepath = sessions_dir / f"{session_id}.json"

        if not filepath.exists():
            return None

        with _file_lock:
            with open(filepath, encoding="utf-8") as f:
                return json.load(f)

    except Exception as e:
        print(f"[Persistence] Failed to read session data: {e}")
        return None


def write_experiment_update(session_id: str, exp_id: str, updates: dict[str, Any]) -> bool:
    """
    Write experiment update directly to JSON file.
    Thread-safe - can be called from background threads.

    Args:
        session_id: Session identifier
        exp_id: Experiment identifier
        updates: Dict of fields to update

    Returns:
        True if successful, False otherwise
    """
    try:
        sessions_dir = get_sessions_directory()
        filepath = sessions_dir / f"{session_id}.json"

        with _file_lock:
            # Read current data
            if not filepath.exists():
                print(f"[Persistence] Session file not found: {session_id}")
                return False

            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            # Find and update experiment
            experiments = data.get("experiments", [])
            found = False
            for exp in experiments:
                if exp["id"] == exp_id:
                    exp.update(updates)
                    found = True
                    break

            if not found:
                print(f"[Persistence] Experiment {exp_id} not found in session {session_id}")
                return False

            # Write back
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        return True

    except Exception as e:
        print(f"[Persistence] Failed to write experiment update: {e}")
        return False


def get_experiment_from_file(session_id: str, exp_id: str) -> dict[str, Any] | None:
    """
    Get experiment data directly from JSON file.
    Thread-safe - can be called from background threads.

    Args:
        session_id: Session identifier
        exp_id: Experiment identifier

    Returns:
        Experiment dict or None if not found
    """
    data = read_session_data(session_id)
    if not data:
        return None

    for exp in data.get("experiments", []):
        if exp["id"] == exp_id:
            return exp

    return None


def get_model_from_file(session_id: str, model_id: str) -> dict[str, Any] | None:
    """
    Get model data directly from JSON file.
    Thread-safe - can be called from background threads.
    """
    data = read_session_data(session_id)
    if not data:
        return None

    for model in data.get("model_library", []):
        if model["id"] == model_id:
            return model

    return None


def get_training_from_file(session_id: str, training_id: str) -> dict[str, Any] | None:
    """
    Get training config directly from JSON file.
    Thread-safe - can be called from background threads.
    """
    data = read_session_data(session_id)
    if not data:
        return None

    for training in data.get("training_library", []):
        if training["id"] == training_id:
            return training

    return None


def get_dataset_config_from_file(session_id: str) -> dict[str, Any]:
    """
    Get dataset config directly from JSON file.
    Thread-safe - can be called from background threads.
    """
    data = read_session_data(session_id)
    if not data:
        return {}

    return data.get("dataset_config", {})


# =============================================================================
# Current Session Persistence (survives page reloads)
# =============================================================================

CURRENT_SESSION_FILE = SESSIONS_DIR / ".current_session"


def get_persisted_session_id() -> str | None:
    """
    Get the persisted session ID from file.
    This survives page reloads and browser refresh.
    """
    try:
        if CURRENT_SESSION_FILE.exists():
            return CURRENT_SESSION_FILE.read_text().strip() or None
    except Exception:
        pass
    return None


def set_persisted_session_id(session_id: str) -> None:
    """
    Persist the current session ID to file.
    This survives page reloads and browser refresh.
    """
    try:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        CURRENT_SESSION_FILE.write_text(session_id)
    except Exception as e:
        print(f"[Persistence] Failed to persist session ID: {e}")
