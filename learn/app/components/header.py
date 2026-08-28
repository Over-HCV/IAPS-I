"""
Header Component
Persistent header with app title, session info, config status, and session controls
"""

from components.styling import inject_custom_css
from components.tooltips import HEADER_TOOLTIPS
from components.utils import clear_session
from state.persistence import (
    list_saved_sessions,
    load_session,
    set_persisted_session_id,
)
from state.workflow import (
    get_session_id,
    has_completed_training,
    has_dataset_config,
    has_models_in_library,
)
import streamlit as st


def render_header():
    """
    Persistent header section shown on all pages
    Contains app title, current session, configuration status, and session controls
    """
    # Apply custom CSS
    inject_custom_css()

    # Row 1: Title and session ID
    col1, _ = st.columns([3, 1])

    with col1:
        st.markdown("### Malware Classification 👾")

    # Row 2: Configuration status + session controls
    status_col, sessions_col, button_col = st.columns([2, 1, 1])

    with status_col:
        # Configuration status indicators
        col1, col2, col3 = st.columns(3)
        with col1:
            icon = "✅" if has_dataset_config() else "⬜"
            st.markdown(f"{icon} Dataset")
        with col2:
            icon = "✅" if has_models_in_library() else "⬜"
            st.markdown(f"{icon} Model")
        with col3:
            icon = "✅" if has_completed_training() else "⬜"
            st.markdown(f"{icon} Training")

    with sessions_col:
        # Past sessions dropdown (functional)
        saved_sessions = list_saved_sessions()
        current_session = get_session_id()

        if saved_sessions or current_session:
            # Create options with current session marked
            options = []
            if current_session:
                options.append(f"{current_session} (current)")
            options.extend([s for s in saved_sessions if s != current_session])

            selected = st.selectbox(
                "Session",
                options=options,
                label_visibility="visible",
                help="Current or load a previous session",
            )

            # Load session if different from current
            is_current = selected.endswith(" (current)")
            if not is_current and selected != current_session:
                if load_session(selected):
                    set_persisted_session_id(selected)
                    st.toast(f"Loaded: {selected}")
                    st.rerun()
        else:
            st.caption("No sessions")

    with button_col:
        # New session button
        if st.button(
            "New Session", width="stretch", help=HEADER_TOOLTIPS["new_session"]
        ):
            clear_session()
            st.rerun()

    st.divider()
