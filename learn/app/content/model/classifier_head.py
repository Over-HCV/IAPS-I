"""
Classifier Head Builder
Mini layer builder for Transfer Learning's classification head (Dense/Dropout/BatchNorm only)
"""

import uuid
import streamlit as st

# Layer types available for classifier head
CLASSIFIER_LAYERS = {
    "GlobalAvgPool": {
        "display_name": "Global Average Pooling",
        "icon": "🔲",
        "params": {},
        "help": "Reduces each feature map to a single value. Usually first layer.",
    },
    "Dense": {
        "display_name": "Dense (Fully Connected)",
        "icon": "🔗",
        "params": {
            "units": {"type": "select", "options": [128, 256, 512, 1024], "default": 512},
            "activation": {"type": "select", "options": ["relu", "gelu", "silu"], "default": "relu"},
        },
        "help": "Fully connected layer. More units = more capacity.",
    },
    "Dropout": {
        "display_name": "Dropout",
        "icon": "💧",
        "params": {
            "rate": {"type": "slider", "min": 0.1, "max": 0.7, "default": 0.3},
        },
        "help": "Randomly drops neurons during training. Prevents overfitting.",
    },
    "BatchNorm": {
        "display_name": "Batch Normalization",
        "icon": "📊",
        "params": {},
        "help": "Normalizes layer inputs. Stabilizes training.",
    },
}

# Default classifier head
DEFAULT_HEAD = [
    {"type": "GlobalAvgPool", "params": {}},
    {"type": "Dense", "params": {"units": 512, "activation": "relu"}},
    {"type": "Dropout", "params": {"rate": 0.3}},
]


def init_classifier_head():
    """Initialize classifier head state"""
    if "classifier_head_layers" not in st.session_state:
        st.session_state.classifier_head_layers = [
            {"id": str(uuid.uuid4())[:8], **layer} for layer in DEFAULT_HEAD
        ]


def render_classifier_head(num_classes: int) -> list[dict]:
    """
    Render the classifier head builder UI.

    Args:
        num_classes: Number of output classes (for auto output layer)

    Returns:
        List of layer configurations
    """
    init_classifier_head()

    st.subheader("Classification Head")
    st.caption("Base model features → [Your layers] → Output")

    # Render current layers
    layers = st.session_state.classifier_head_layers

    for i, layer in enumerate(layers):
        _render_layer_row(i, layer, len(layers))

    # Auto output layer (not editable)
    with st.container(border=True):
        st.markdown(f"**Output** • Dense({num_classes}, Softmax) • *auto*")

    st.divider()

    # Add layer section
    _render_add_layer()

    # Reset to default
    if st.button("Reset to Default", help="Reset to default classifier head"):
        st.session_state.classifier_head_layers = [
            {"id": str(uuid.uuid4())[:8], **layer} for layer in DEFAULT_HEAD
        ]
        st.rerun()

    return st.session_state.classifier_head_layers


def _render_layer_row(index: int, layer: dict, total: int):
    """Render a single layer row"""
    layer_id = layer["id"]
    layer_type = layer["type"]
    layer_info = CLASSIFIER_LAYERS.get(layer_type, {})

    with st.container(border=True):
        col_info, col_actions = st.columns([4, 1])

        with col_info:
            # Layer display
            icon = layer_info.get("icon", "📦")
            name = layer_info.get("display_name", layer_type)
            params_str = _format_params(layer.get("params", {}))

            st.markdown(f"**{icon} {name}** {params_str}")

        with col_actions:
            btn_cols = st.columns(3)

            # Move up
            with btn_cols[0]:
                if index > 0:
                    if st.button("↑", key=f"up_{layer_id}", help="Move up"):
                        _move_layer(index, -1)
                        st.rerun()

            # Move down
            with btn_cols[1]:
                if index < total - 1:
                    if st.button("↓", key=f"down_{layer_id}", help="Move down"):
                        _move_layer(index, 1)
                        st.rerun()

            # Delete
            with btn_cols[2]:
                if st.button("🗑️", key=f"del_{layer_id}", help="Delete"):
                    _delete_layer(index)
                    st.rerun()

        # Inline parameter editor (if has params)
        if layer_info.get("params"):
            _render_param_editor(index, layer, layer_info)


def _render_param_editor(index: int, layer: dict, layer_info: dict):
    """Render inline parameter editor"""
    params_def = layer_info.get("params", {})
    current_params = layer.get("params", {})

    cols = st.columns(len(params_def))

    for i, (param_name, param_def) in enumerate(params_def.items()):
        with cols[i]:
            current_value = current_params.get(param_name, param_def.get("default"))

            if param_def["type"] == "select":
                options = param_def["options"]
                new_value = st.selectbox(
                    param_name.title(),
                    options=options,
                    index=options.index(current_value) if current_value in options else 0,
                    key=f"param_{layer['id']}_{param_name}",
                )
            elif param_def["type"] == "slider":
                new_value = st.slider(
                    param_name.title(),
                    min_value=param_def["min"],
                    max_value=param_def["max"],
                    value=current_value,
                    key=f"param_{layer['id']}_{param_name}",
                )
            else:
                new_value = current_value

            # Update if changed
            if new_value != current_value:
                st.session_state.classifier_head_layers[index]["params"][param_name] = new_value


def _render_add_layer():
    """Render add layer section"""
    col1, col2 = st.columns([3, 1])

    with col1:
        layer_options = {k: f"{v['icon']} {v['display_name']}" for k, v in CLASSIFIER_LAYERS.items()}

        selected_type = st.selectbox(
            "Add Layer",
            options=list(layer_options.keys()),
            format_func=lambda x: layer_options[x],
            key="new_classifier_layer",
            help="Select layer type to add",
        )

    with col2:
        st.write("")  # Spacing
        if st.button("+ Add", width="stretch"):
            _add_layer(selected_type)
            st.rerun()


def _add_layer(layer_type: str):
    """Add a new layer"""
    layer_info = CLASSIFIER_LAYERS.get(layer_type, {})
    default_params = {
        name: param.get("default") for name, param in layer_info.get("params", {}).items()
    }

    new_layer = {
        "id": str(uuid.uuid4())[:8],
        "type": layer_type,
        "params": default_params,
    }

    st.session_state.classifier_head_layers.append(new_layer)


def _delete_layer(index: int):
    """Delete a layer"""
    st.session_state.classifier_head_layers.pop(index)


def _move_layer(index: int, direction: int):
    """Move a layer up or down"""
    layers = st.session_state.classifier_head_layers
    new_index = index + direction

    if 0 <= new_index < len(layers):
        layers[index], layers[new_index] = layers[new_index], layers[index]


def _format_params(params: dict) -> str:
    """Format parameters for display"""
    if not params:
        return ""

    parts = []
    for key, value in params.items():
        if isinstance(value, float):
            parts.append(f"{value:.2f}")
        else:
            parts.append(str(value))

    return f"({', '.join(parts)})"


def export_classifier_head() -> list[dict]:
    """Export classifier head configuration"""
    return [
        {"type": layer["type"], "params": layer.get("params", {})}
        for layer in st.session_state.get("classifier_head_layers", [])
    ]
