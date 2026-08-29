"""Tabular MLP configuration UI"""

import streamlit as st

from models.pytorch.mlp import ACTIVATIONS, DEFAULT_ACTIVATION

LAYER_WIDTH_OPTIONS = [16, 32, 64, 128, 256, 512, 1024]
DEFAULT_HIDDEN_WIDTHS = [128, 64]
MAX_HIDDEN_LAYERS = 5


def render(num_classes: int, input_dim: int) -> dict:
    """Configure a dense network over encoded feature columns"""
    st.header("Tabular MLP Configuration")

    if input_dim <= 0:
        st.warning(
            "Save the dataset configuration first so the encoded feature count "
            "is known."
        )

    _init_defaults()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Input Features", input_dim)
    with col2:
        st.metric("Output Classes", num_classes)

    st.divider()

    hidden_layers = _render_hidden_layers()
    st.divider()
    regularization = _render_regularization()

    config = {
        "input_dim": input_dim,
        "hidden_layers": hidden_layers,
        **regularization,
        "num_classes": num_classes,
        "is_valid": input_dim > 0 and bool(hidden_layers),
    }

    _render_shape_summary(input_dim, hidden_layers, num_classes)

    return config


def _init_defaults() -> None:
    """Seed widget defaults before the widgets render"""
    defaults = {
        "mlp_num_layers": len(DEFAULT_HIDDEN_WIDTHS),
        "mlp_activation": DEFAULT_ACTIVATION,
        "mlp_dropout": 0.2,
        "mlp_batch_norm": True,
    }
    for index, width in enumerate(DEFAULT_HIDDEN_WIDTHS):
        defaults[f"mlp_layer_{index}"] = width

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_hidden_layers() -> list[int]:
    """Choose the depth and the width of each hidden layer"""
    st.subheader("Hidden Layers")

    num_layers = st.slider(
        "Number of hidden layers",
        min_value=1,
        max_value=MAX_HIDDEN_LAYERS,
        key="mlp_num_layers",
        help="Depth of the network, excluding the output layer",
    )

    widths = []
    columns = st.columns(num_layers)

    for index in range(num_layers):
        key = f"mlp_layer_{index}"
        if key not in st.session_state:
            # New layers start narrower than the one before them
            previous = widths[-1] if widths else DEFAULT_HIDDEN_WIDTHS[0]
            st.session_state[key] = max(previous // 2, LAYER_WIDTH_OPTIONS[0])

        with columns[index]:
            widths.append(
                st.selectbox(
                    f"Layer {index + 1}",
                    LAYER_WIDTH_OPTIONS,
                    key=key,
                    help="Number of units in this layer",
                )
            )

    return widths


def _render_regularization() -> dict:
    """Dropout, batch norm and activation"""
    st.subheader("Activation & Regularization")

    col1, col2, col3 = st.columns(3)

    with col1:
        activation = st.selectbox(
            "Activation",
            list(ACTIVATIONS),
            key="mlp_activation",
            help="Applied after every hidden layer",
        )
    with col2:
        dropout = st.slider(
            "Dropout",
            min_value=0.0,
            max_value=0.8,
            step=0.05,
            key="mlp_dropout",
            help="Fraction of units dropped during training. 0 disables it",
        )
    with col3:
        st.markdown("<div style='height: 1.8rem'></div>", unsafe_allow_html=True)
        batch_norm = st.checkbox(
            "Batch normalization",
            key="mlp_batch_norm",
            help="Normalize activations between layers; usually speeds up training",
        )

    return {
        "activation": activation,
        "dropout": dropout,
        "batch_norm": batch_norm,
    }


def _render_shape_summary(
    input_dim: int, hidden_layers: list[int], num_classes: int
) -> None:
    """Show the layer widths end to end"""
    shape = " → ".join(
        str(size) for size in [input_dim, *hidden_layers, num_classes]
    )
    st.caption(f"Network shape: {shape}")
