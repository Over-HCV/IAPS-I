"""
UI State Management
User interface preferences and theme settings
"""

from typing import TypedDict

import streamlit as st


class UIState(TypedDict, total=False):
    """Type definition for UI state fields"""

    theme_primary: str
    theme_secondary: str
    theme_background: str
    past_sessions: list[str]


# Default theme colors
DEFAULT_PRIMARY = "#bdd373"
DEFAULT_SECONDARY = "#8fd7d7"
DEFAULT_BACKGROUND = "#0e1117"


def init_ui_state() -> None:
    """Initialize UI state with default values"""
    if "theme_primary" not in st.session_state:
        st.session_state.theme_primary = DEFAULT_PRIMARY

    if "theme_secondary" not in st.session_state:
        st.session_state.theme_secondary = DEFAULT_SECONDARY

    if "theme_background" not in st.session_state:
        st.session_state.theme_background = DEFAULT_BACKGROUND

    if "past_sessions" not in st.session_state:
        st.session_state.past_sessions = []


# Theme Management
def get_theme_primary() -> str:
    """Get primary theme color"""
    return st.session_state.get("theme_primary", DEFAULT_PRIMARY)


def set_theme_primary(color: str) -> None:
    """Set primary theme color"""
    st.session_state.theme_primary = color


def get_theme_secondary() -> str:
    """Get secondary theme color"""
    return st.session_state.get("theme_secondary", DEFAULT_SECONDARY)


def set_theme_secondary(color: str) -> None:
    """Set secondary theme color"""
    st.session_state.theme_secondary = color


def get_theme_background() -> str:
    """Get background theme color"""
    return st.session_state.get("theme_background", DEFAULT_BACKGROUND)


def set_theme_background(color: str) -> None:
    """Set background theme color"""
    st.session_state.theme_background = color


def get_theme_colors() -> tuple[str, str, str]:
    """Get all theme colors as tuple (primary, secondary, background)"""
    return (get_theme_primary(), get_theme_secondary(), get_theme_background())


def set_theme_colors(primary: str, secondary: str, background: str) -> None:
    """Set all theme colors at once"""
    st.session_state.theme_primary = primary
    st.session_state.theme_secondary = secondary
    st.session_state.theme_background = background


def reset_theme_to_defaults() -> None:
    """Reset theme colors to default values"""
    set_theme_colors(DEFAULT_PRIMARY, DEFAULT_SECONDARY, DEFAULT_BACKGROUND)


# Session History Management
def get_past_sessions() -> list[str]:
    """Get list of past session IDs"""
    return st.session_state.get("past_sessions", [])


def add_past_session(session_id: str) -> None:
    """Add a session ID to past sessions"""
    if "past_sessions" not in st.session_state:
        st.session_state.past_sessions = []

    if session_id not in st.session_state.past_sessions:
        st.session_state.past_sessions.append(session_id)


def clear_past_sessions() -> None:
    """Clear all past sessions"""
    st.session_state.past_sessions = []


def clear_ui_state() -> None:
    """Clear UI-related session state"""
    keys_to_clear = [
        "theme_primary",
        "theme_secondary",
        "theme_background",
        "past_sessions",
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    # Reinitialize with defaults
    init_ui_state()
