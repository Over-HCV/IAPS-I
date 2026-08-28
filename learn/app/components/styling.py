"""
Styling Component
Custom CSS injection for professional styling
"""

from constants import GET_CSS
from state.ui import get_theme_colors
import streamlit as st


def inject_custom_css():
    """
    Inject custom CSS for professional styling
    """
    # Get theme colors from state
    primary, secondary, background = get_theme_colors()

    st.markdown(GET_CSS(primary, secondary, background), unsafe_allow_html=True)
