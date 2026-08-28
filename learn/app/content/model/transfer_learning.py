"""Transfer Learning configuration UI"""

from config import PRETRAINED_MODELS
from content.model.classifier_head import export_classifier_head, render_classifier_head
import streamlit as st


def _init_state():
    """Initialize transfer learning session state defaults"""
    if "transfer_base_model" not in st.session_state:
        st.session_state.transfer_base_model = "ResNet50"
    if "transfer_weights" not in st.session_state:
        st.session_state.transfer_weights = "ImageNet"
    if "transfer_strategy" not in st.session_state:
        st.session_state.transfer_strategy = "Feature Extraction"
    if "transfer_unfreeze_layers" not in st.session_state:
        st.session_state.transfer_unfreeze_layers = 10


def render(num_classes: int) -> dict:
    """Configure Transfer Learning model"""
    _init_state()

    st.header("Transfer Learning Configuration")

    # Base Model Selection
    st.subheader("Pre-trained Model (Feature Extractor)")

    col1, col2 = st.columns(2)

    with col1:
        base_model = st.selectbox(
            "Select Base Model",
            options=PRETRAINED_MODELS,
            key="transfer_base_model",
            help="Pre-trained CNN backbone that extracts features. ResNet50 is a solid default.",
        )

    with col2:
        weights = st.radio(
            "Initial Weights",
            ["ImageNet", "Random"],
            key="transfer_weights",
            help="ImageNet: Pre-trained on 1M+ images (recommended). Random: Train from scratch.",
        )

    # Fine-tuning Strategy
    st.subheader("Fine-tuning Strategy")

    strategy = st.radio(
        "Training Strategy",
        ["Feature Extraction", "Partial Fine-tuning", "Full Fine-tuning"],
        key="transfer_strategy",
        horizontal=True,
        help="Feature Extraction: Freeze base, train only classifier. Partial: Unfreeze top layers. Full: Train everything.",
    )

    unfreeze_layers = 0
    if strategy == "Partial Fine-tuning":
        unfreeze_layers = st.slider(
            "Number of Layers to Unfreeze",
            min_value=0,
            max_value=50,
            key="transfer_unfreeze_layers",
            help="How many layers from the top to make trainable. Start with 10-20.",
        )

    st.divider()

    # Classification Head (mini layer builder)
    classifier_layers = render_classifier_head(num_classes)

    return {
        "base_model": base_model,
        "weights": weights,
        "strategy": strategy,
        "unfreeze_layers": unfreeze_layers if strategy == "Partial Fine-tuning" else 0,
        "classifier_head": export_classifier_head(),
        "num_classes": num_classes,
    }
