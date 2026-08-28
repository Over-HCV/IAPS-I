"""
Layer Builder - Functions to manipulate the layer stack in session state
"""

import streamlit as st
import uuid
from typing import Any
import copy

from content.model.layer_configs import PRESETS, get_default_params


def init_layer_stack():
    """Initialize layer stack in session state with default preset"""
    if "layer_stack" not in st.session_state:
        load_preset("profesor")

    if "selected_preset" not in st.session_state:
        st.session_state.selected_preset = "profesor"

    if "editing_layer_id" not in st.session_state:
        st.session_state.editing_layer_id = None


def get_layer_stack() -> list[dict]:
    """Get current layer stack from session state"""
    return st.session_state.get("layer_stack", [])


def set_layer_stack(layers: list[dict]):
    """Set the entire layer stack"""
    st.session_state.layer_stack = layers


def generate_layer_id() -> str:
    """Generate a unique ID for a layer"""
    return f"layer_{uuid.uuid4().hex[:8]}"


def add_layer(layer_type: str, params: dict[str, Any] | None = None, position: int | None = None):
    """
    Add a new layer to the stack.
    If position is None, adds at the end.
    """
    if params is None:
        params = get_default_params(layer_type)

    new_layer = {
        "id": generate_layer_id(),
        "type": layer_type,
        "params": params.copy()
    }

    layer_stack = get_layer_stack()

    if position is None or position >= len(layer_stack):
        layer_stack.append(new_layer)
    else:
        layer_stack.insert(position, new_layer)

    set_layer_stack(layer_stack)
    st.session_state.selected_preset = "custom"


def remove_layer(layer_id: str):
    """Remove a layer from the stack by ID"""
    layer_stack = get_layer_stack()
    layer_stack = [l for l in layer_stack if l["id"] != layer_id]
    set_layer_stack(layer_stack)
    st.session_state.selected_preset = "custom"


def move_layer_up(layer_id: str):
    """Move a layer one position up (earlier in the stack)"""
    layer_stack = get_layer_stack()

    for i, layer in enumerate(layer_stack):
        if layer["id"] == layer_id and i > 0:
            layer_stack[i], layer_stack[i - 1] = layer_stack[i - 1], layer_stack[i]
            break

    set_layer_stack(layer_stack)
    st.session_state.selected_preset = "custom"


def move_layer_down(layer_id: str):
    """Move a layer one position down (later in the stack)"""
    layer_stack = get_layer_stack()

    for i, layer in enumerate(layer_stack):
        if layer["id"] == layer_id and i < len(layer_stack) - 1:
            layer_stack[i], layer_stack[i + 1] = layer_stack[i + 1], layer_stack[i]
            break

    set_layer_stack(layer_stack)
    st.session_state.selected_preset = "custom"


def update_layer(layer_id: str, new_params: dict[str, Any]):
    """Update parameters of an existing layer"""
    layer_stack = get_layer_stack()

    for layer in layer_stack:
        if layer["id"] == layer_id:
            layer["params"].update(new_params)
            break

    set_layer_stack(layer_stack)
    st.session_state.selected_preset = "custom"


def duplicate_layer(layer_id: str):
    """Duplicate a layer and insert it right after the original"""
    layer_stack = get_layer_stack()

    for i, layer in enumerate(layer_stack):
        if layer["id"] == layer_id:
            new_layer = {
                "id": generate_layer_id(),
                "type": layer["type"],
                "params": copy.deepcopy(layer["params"])
            }
            layer_stack.insert(i + 1, new_layer)
            break

    set_layer_stack(layer_stack)
    st.session_state.selected_preset = "custom"


def load_preset(preset_name: str):
    """Load a preset architecture into the layer stack"""
    if preset_name not in PRESETS:
        return

    preset = PRESETS[preset_name]
    layers = []

    for layer_def in preset["layers"]:
        layers.append({
            "id": generate_layer_id(),
            "type": layer_def["type"],
            "params": layer_def["params"].copy()
        })

    set_layer_stack(layers)
    st.session_state.selected_preset = preset_name


def clear_layer_stack():
    """Remove all layers from the stack"""
    set_layer_stack([])
    st.session_state.selected_preset = "empty"


def get_layer_by_id(layer_id: str) -> dict | None:
    """Get a layer by its ID"""
    for layer in get_layer_stack():
        if layer["id"] == layer_id:
            return layer
    return None


def get_layer_index(layer_id: str) -> int:
    """Get the index of a layer in the stack"""
    for i, layer in enumerate(get_layer_stack()):
        if layer["id"] == layer_id:
            return i
    return -1


def start_editing(layer_id: str):
    """Start editing a layer"""
    st.session_state.editing_layer_id = layer_id


def stop_editing():
    """Stop editing any layer"""
    st.session_state.editing_layer_id = None


def is_editing(layer_id: str) -> bool:
    """Check if a specific layer is being edited"""
    return st.session_state.get("editing_layer_id") == layer_id


def export_layer_stack() -> dict:
    """Export layer stack as a configuration dict for saving"""
    return {
        "layers": [
            {"type": l["type"], "params": l["params"]}
            for l in get_layer_stack()
        ],
        "preset": st.session_state.get("selected_preset", "custom")
    }


def import_layer_stack(config: dict):
    """Import a layer stack from a saved configuration"""
    layers = []
    for layer_def in config.get("layers", []):
        layers.append({
            "id": generate_layer_id(),
            "type": layer_def["type"],
            "params": layer_def.get("params", {})
        })

    set_layer_stack(layers)
    st.session_state.selected_preset = config.get("preset", "custom")
