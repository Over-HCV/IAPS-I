"""
Sidebar Component
Persistent sidebar showing system resources, theme settings, and session actions
"""

from components.theme import render_theme_settings
from components.tooltips import SIDEBAR_TOOLTIPS
from components.utils import (
    get_compute_device,
    get_cpu_info,
    get_gpu_memory,
    get_platform_info,
    get_system_memory,
)
import streamlit as st


def render_sidebar():
    """
    Persistent sidebar shown on all pages
    Shows system resources, theme settings, and delete session button
    """
    st.sidebar.header("System Resources", help=SIDEBAR_TOOLTIPS["system_resources"])

    device = get_compute_device()
    cpu_info = get_cpu_info()

    # Row 1: Compute device
    st.sidebar.caption(f"**{device['type']}** · {device['name']}")

    # Row 2: Memory metrics
    gpu_mem = get_gpu_memory()
    sys_mem = get_system_memory()
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.caption("GPU Mem", help=SIDEBAR_TOOLTIPS["gpu_memory"])
        st.markdown(f"**{gpu_mem}**")
    with col2:
        st.caption("RAM", help=SIDEBAR_TOOLTIPS["system_ram"])
        st.markdown(f"**{sys_mem}**")

    # Row 3: CPU and platform
    platform_str = get_platform_info()
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.caption("CPU", help=SIDEBAR_TOOLTIPS["cpu_info"])
        st.markdown(f"**{cpu_info['cores']}C/{cpu_info['threads']}T**")
    with col2:
        st.caption("Platform", help=SIDEBAR_TOOLTIPS["platform"])
        st.markdown(f"**{platform_str}**")

    st.sidebar.divider()

    render_theme_settings()

    st.sidebar.divider()

    # Delete Session button at bottom
    if st.sidebar.button(
        "Delete Session",
        type="secondary",
        width="stretch",
        help="Delete current session and start fresh",
    ):
        _handle_delete_session()


def _handle_delete_session():
    """Handle delete session button click"""
    from state.persistence import delete_session
    from state.workflow import clear_workflow_state, get_session_id

    session_id = get_session_id()
    if session_id:
        delete_session(session_id)
        clear_workflow_state()
        st.rerun()
