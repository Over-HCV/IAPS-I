"""Model configuration summary and save functionality"""

from datetime import datetime
from typing import Any

from state.workflow import save_model_config
import streamlit as st


def build_config(
    model_type: str,
    num_classes: int,
    cnn_config: dict | None,
    transfer_config: dict | None,
    transformer_config: dict | None,
) -> dict[str, Any]:
    """Build complete model configuration"""
    config = {
        "model_type": model_type,
        "num_classes": num_classes,
        "timestamp": datetime.now().isoformat(),
    }

    if model_type == "Custom CNN" and cnn_config:
        num_layers = len(cnn_config.get("layers", []))
        config["architecture"] = f"CNN_{num_layers}_layers"
        config["cnn_config"] = cnn_config
        config["implementation"] = "pytorch"

    elif model_type == "Transfer Learning" and transfer_config:
        config["architecture"] = (
            f"{transfer_config['base_model']}_{transfer_config['strategy'].replace(' ', '_')}"
        )
        config["transfer_config"] = transfer_config
        config["implementation"] = "pytorch"

    elif model_type == "Transformer" and transformer_config:
        config["architecture"] = (
            f"ViT_D{transformer_config['depth']}_H{transformer_config['num_heads']}"
        )
        config["transformer_config"] = transformer_config
        config["implementation"] = "manual"

    return config


def render_summary(model_config: dict[str, Any]):
    """Display model architecture summary"""
    st.header("Model Architecture Summary")

    # Basic Info
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Model Type", model_config["model_type"])
    with col2:
        st.metric("Architecture", model_config["architecture"])
    with col3:
        st.metric("Output Classes", model_config["num_classes"])

    # Model-specific details
    if model_config["model_type"] == "Custom CNN":
        cnn_cfg = model_config.get("cnn_config", {})
        layers = cnn_cfg.get("layers", [])
        st.write(f"**Total Layers:** {len(layers)}")

        layer_counts = {}
        for layer in layers:
            lt = layer["type"]
            layer_counts[lt] = layer_counts.get(lt, 0) + 1

        if layer_counts:
            counts_str = ", ".join(
                [f"{count} {ltype}" for ltype, count in layer_counts.items()]
            )
            st.write(f"**Layer Composition:** {counts_str}")

    elif model_config["model_type"] == "Transfer Learning":
        transfer_cfg = model_config["transfer_config"]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Base Model:** {transfer_cfg['base_model']}")
        with col2:
            st.write(f"**Weights:** {transfer_cfg['weights']}")
        with col3:
            st.write(f"**Strategy:** {transfer_cfg['strategy']}")

        # Show classifier head layers
        classifier_head = transfer_cfg.get("classifier_head", [])
        if classifier_head:
            head_str = " → ".join([layer["type"] for layer in classifier_head])
            st.write(f"**Classifier Head:** {head_str} → Output")

    elif model_config["model_type"] == "Transformer":
        col1, col2, col3, col4 = st.columns(4)
        transformer_cfg = model_config["transformer_config"]
        with col1:
            st.write(
                f"**Patch Size:** {transformer_cfg['patch_size']}x{transformer_cfg['patch_size']}"
            )
        with col2:
            st.write(f"**Embedding Dim:** {transformer_cfg['embed_dim']}")
        with col3:
            st.write(f"**Depth:** {transformer_cfg['depth']} layers")
        with col4:
            st.write(f"**Attention Heads:** {transformer_cfg['num_heads']}")

    # Placeholder for actual model metrics
    st.subheader("Model Metrics")
    st.info("Model metrics will be calculated when the model is built during training")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Parameters", "Will be calculated")
    with col2:
        st.metric("Trainable Parameters", "Will be calculated")
    with col3:
        st.metric("Model Size", "Will be calculated")


def render_save(model_config: dict[str, Any]):
    """Save model configuration"""
    st.header("Save Configuration")

    # Check validation for Custom CNN
    is_valid = True
    if model_config["model_type"] == "Custom CNN":
        cnn_cfg = model_config.get("cnn_config", {})
        is_valid = cnn_cfg.get("is_valid", False)

    col1, col2 = st.columns([3, 1])

    with col1:
        if is_valid:
            st.success("Model configuration is ready!")
        else:
            st.warning("Fix validation errors before saving")

        with st.expander("View Full Configuration", expanded=False):
            st.json(model_config)

    with col2:
        if st.button(
            "Save Model Config",
            type="primary",
            width="stretch",
            disabled=not is_valid,
        ):
            save_model_config(model_config)
            st.success("Model configuration saved!")
            st.balloons()

            st.info("You can now proceed to Training Configuration")
