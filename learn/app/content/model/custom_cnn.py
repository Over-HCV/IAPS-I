"""Custom CNN configuration UI"""

from content.model.layer_builder import export_layer_stack, init_layer_stack
from content.model.layer_renderer import (
    render_add_layer_section,
    render_layer_stack,
    render_output_layer,
    render_preset_selector,
    render_validation_status,
)
import streamlit as st


def render(num_classes: int) -> dict:
    """Configure Custom CNN using the layer builder"""
    init_layer_stack()

    st.header("Custom CNN Configuration")

    render_preset_selector()

    st.markdown("---")

    render_layer_stack()

    render_output_layer(num_classes)

    st.markdown("---")

    render_add_layer_section()

    is_valid = render_validation_status()

    layer_config = export_layer_stack()
    layer_config["num_classes"] = num_classes
    layer_config["is_valid"] = is_valid

    return layer_config
