"""
Theme Component
Theme customization settings
"""

from state.ui import (
    get_theme_background,
    get_theme_primary,
    get_theme_secondary,
    set_theme_background,
    set_theme_colors,
    set_theme_primary,
    set_theme_secondary,
)
import streamlit as st


def render_theme_settings():
    """
    Theme customization settings
    """
    with st.sidebar.expander("Theme Settings"):
        st.markdown("**Color Palette**")

        # Color pickers (no key, manual state management)
        primary = st.color_picker("Primary (buttons, links)", value=get_theme_primary())
        if primary != get_theme_primary():
            set_theme_primary(primary)
            st.rerun()

        secondary = st.color_picker("Secondary (headers)", value=get_theme_secondary())
        if secondary != get_theme_secondary():
            set_theme_secondary(secondary)
            st.rerun()

        background = st.color_picker("Background", value=get_theme_background())
        if background != get_theme_background():
            set_theme_background(background)
            st.rerun()

        # Presets (softer colors from image)
        st.markdown("**Presets**")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Soft Green", width="stretch"):
                set_theme_colors("#98c127", "#bdd373", "#0e1117")
                st.rerun()

        with col2:
            if st.button("Soft Blue", width="stretch"):
                set_theme_colors("#8fd7d7", "#00b0be", "#0e1117")
                st.rerun()

        col3, col4 = st.columns(2)
        with col3:
            if st.button("Soft Pink", width="stretch"):
                set_theme_colors("#f45f74", "#ff8ca1", "#0e1117")
                st.rerun()

        with col4:
            if st.button("Soft Orange", width="stretch"):
                set_theme_colors("#ffb255", "#ffcd8e", "#0e1117")
                st.rerun()
