"""Model Configuration Page - Main Orchestrator with Library"""

from components.model_card import render_model_library
from content.model import custom_cnn, summary, transfer_learning, transformer
from content.model.tooltips import MODEL_TYPES
from state.workflow import (
    add_model_to_library,
    delete_model_from_library,
    get_dataset_config,
    get_model_from_library,
    get_model_library,
    has_dataset_config,
    update_model_in_library,
)
import streamlit as st


def render():
    """Main render function for Model page"""
    st.title("Model Configuration", help="Design and save neural network architectures for malware classification.")

    if not has_dataset_config():
        st.warning("Please configure dataset first to determine number of classes")
        st.stop()

    dataset_config = get_dataset_config()
    num_classes = len(dataset_config.get("selected_families", []))

    if num_classes == 0:
        st.error("Dataset has no classes configured")
        st.stop()

    # Initialize editor state
    if "model_editor_mode" not in st.session_state:
        st.session_state.model_editor_mode = None  # None, "new", or model_id
    if "model_editor_name" not in st.session_state:
        st.session_state.model_editor_name = ""

    # Section 1: Model Library
    _render_model_library()

    st.divider()

    # Section 2: Model Editor (if active)
    if st.session_state.model_editor_mode is not None:
        _render_model_editor(num_classes)


def _render_model_library():
    """Render the model library with cards"""
    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("Model Library")

    with col2:
        if st.button("+ New Model", type="primary", width="stretch"):
            st.session_state.model_editor_mode = "new"
            st.session_state.model_editor_name = ""
            st.rerun()

    models = get_model_library()

    render_model_library(
        models=models,
        selected_id=st.session_state.get("model_editor_mode")
        if st.session_state.get("model_editor_mode") != "new"
        else None,
        on_select=_handle_model_select,
        on_edit=_handle_model_edit,
        on_delete=_handle_model_delete,
        cards_per_row=3,
    )


def _handle_model_select(model_id: str):
    """Handle model card selection"""
    st.session_state.model_editor_mode = model_id
    model = get_model_from_library(model_id)
    if model:
        st.session_state.model_editor_name = model["name"]
        # Load model config into editor state
        _load_model_into_editor(model)
    st.rerun()


def _handle_model_edit(model_id: str):
    """Handle edit button click"""
    _handle_model_select(model_id)


def _handle_model_delete(model_id: str):
    """Handle delete button click"""
    delete_model_from_library(model_id)
    if st.session_state.model_editor_mode == model_id:
        st.session_state.model_editor_mode = None
    st.rerun()


def _load_model_into_editor(model: dict):
    """Load model config into session state for editing"""
    config = model.get("config", {})
    model_type = config.get("model_type", "Custom CNN")

    # Set model type
    st.session_state.model_type = model_type

    # Load type-specific config
    if model_type == "Transfer Learning":
        transfer_cfg = config.get("transfer_config", {})
        st.session_state.transfer_base_model = transfer_cfg.get("base_model", "ResNet50")
        st.session_state.transfer_weights = transfer_cfg.get("weights", "ImageNet")
        st.session_state.transfer_strategy = transfer_cfg.get(
            "strategy", "Feature Extraction"
        )
        st.session_state.transfer_unfreeze_layers = transfer_cfg.get(
            "unfreeze_layers", 10
        )
        st.session_state.transfer_global_pooling = transfer_cfg.get(
            "global_pooling", True
        )
        st.session_state.transfer_add_dense = transfer_cfg.get("add_dense", True)
        st.session_state.transfer_dense_units = transfer_cfg.get("dense_units", 512)
        st.session_state.transfer_dropout = transfer_cfg.get("dropout", 0.5)

    elif model_type == "Transformer":
        transformer_cfg = config.get("transformer_config", {})
        st.session_state.transformer_patch_size = transformer_cfg.get("patch_size", 16)
        st.session_state.transformer_embed_dim = transformer_cfg.get("embed_dim", 768)
        st.session_state.transformer_depth = transformer_cfg.get("depth", 12)
        st.session_state.transformer_num_heads = transformer_cfg.get("num_heads", 12)
        st.session_state.transformer_mlp_ratio = transformer_cfg.get("mlp_ratio", 4.0)
        st.session_state.transformer_dropout = transformer_cfg.get("dropout", 0.1)


def _render_model_editor(num_classes: int):
    """Render the model editor section"""
    is_new = st.session_state.model_editor_mode == "new"

    # Header with close button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.header("New Model" if is_new else "Edit Model")
    with col2:
        if st.button("✕ Close", width="stretch"):
            st.session_state.model_editor_mode = None
            st.rerun()

    # Model name input
    model_name = st.text_input(
        "Model Name",
        value=st.session_state.model_editor_name,
        placeholder="e.g., ResNet50_v1",
        help="Give your model a memorable name",
    )
    st.session_state.model_editor_name = model_name

    st.divider()

    # Model type selection
    model_type = _render_model_type_selection()

    # Architecture configuration
    cnn_config = None
    transformer_config = None
    transfer_config = None

    if model_type == "Custom CNN":
        cnn_config = custom_cnn.render(num_classes)
    elif model_type == "Transformer":
        transformer_config = transformer.render(num_classes)
    else:  # Transfer Learning
        transfer_config = transfer_learning.render(num_classes)

    # Build config
    model_config = summary.build_config(
        model_type, num_classes, cnn_config, transfer_config, transformer_config
    )

    if model_config:
        summary.render_summary(model_config)

        # Save to library button
        st.divider()
        _render_save_to_library(model_name, model_config, is_new)


def _render_model_type_selection():
    """Section: Choose model architecture type"""
    st.subheader("Architecture Type", help="Choose the neural network architecture for your model.")

    model_type = st.segmented_control(
        "Select Model Type",
        options=["Custom CNN", "Transformer", "Transfer Learning"],
        default="Custom CNN",
        key="model_type",
    )

    # Use tooltips from centralized file
    descriptions = {
        "Custom CNN": f"🔧 **{MODEL_TYPES['custom_cnn']['name']}**: {MODEL_TYPES['custom_cnn']['description']}",
        "Transformer": f"🧪 **{MODEL_TYPES['transformer']['name']}**: {MODEL_TYPES['transformer']['description']}",
        "Transfer Learning": f"🎯 **{MODEL_TYPES['transfer_learning']['name']}**: {MODEL_TYPES['transfer_learning']['description']}",
    }

    st.info(descriptions.get(model_type, ""))

    return model_type


def _render_save_to_library(model_name: str, model_config: dict, is_new: bool):
    """Render the save to library section"""
    col1, col2 = st.columns([3, 1])

    with col1:
        if not model_name.strip():
            st.warning("Please enter a model name")

    with col2:
        # Check validation for Custom CNN
        is_valid = True
        if model_config.get("model_type") == "Custom CNN":
            cnn_cfg = model_config.get("cnn_config", {})
            is_valid = cnn_cfg.get("is_valid", False)

        can_save = bool(model_name.strip()) and is_valid

        button_text = "Save to Library" if is_new else "Update Model"

        if st.button(
            button_text,
            type="primary",
            width="stretch",
            disabled=not can_save,
        ):
            if is_new:
                add_model_to_library(model_name.strip(), model_config)
                st.success(f"Model '{model_name}' saved to library!")
            else:
                model_id = st.session_state.model_editor_mode
                update_model_in_library(model_id, model_name.strip(), model_config)
                st.success(f"Model '{model_name}' updated!")

            st.session_state.model_editor_mode = None
            st.rerun()
