"""Grad-CAM visualization section for interpretability page."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st

from content.interpret.engine.data_loader import get_test_dataloader, get_test_samples
from content.interpret.engine.gradcam import (
    compute_gradcam,
    get_conv_layers,
    get_top_predictions,
)
from content.interpret.engine.model_loader import load_experiment_model
from content.interpret.tooltips import GRADCAM_TOOLTIPS
from state.persistence import get_dataset_config_from_file
from state.workflow import get_session_id
from training.transforms import create_val_transforms


def render_gradcam(exp_id: str):
    """Section: Grad-CAM visualization"""
    st.header("Grad-CAM: What the Model Sees", help=GRADCAM_TOOLTIPS["method"])

    try:
        model, device, _ = load_experiment_model(exp_id)
        _, class_names = get_test_dataloader(batch_size=1)

        conv_layers = get_conv_layers(model)
        if not conv_layers:
            st.warning("No convolutional layers found in model")
            return

        layer_names = [name for name, _ in conv_layers]

        col1, col2 = st.columns(2)

        with col1:
            samples = get_test_samples(n_samples=20)
            sample_options = {
                f"{s['class_name']} (idx {s['index']})": s for s in samples
            }
            selected_sample_name = st.selectbox(
                "Select Sample",
                options=list(sample_options.keys()),
                key="gradcam_sample_select",
                help="Choose a test image to analyze.",
            )
            selected_sample = sample_options[selected_sample_name]

        with col2:
            selected_layer_name = st.selectbox(
                "Target Layer",
                options=layer_names,
                index=len(layer_names) - 1,
                key="gradcam_layer_select",
                help=GRADCAM_TOOLTIPS["target_layer"],
            )
            target_layer = dict(conv_layers)[selected_layer_name]

        opacity = st.slider(
            "Overlay Opacity", 0.0, 1.0, 0.5,
            key="gradcam_opacity",
            help=GRADCAM_TOOLTIPS["opacity"],
        )

        if st.button("Generate Grad-CAM", key="gradcam_run"):
            with st.spinner("Computing Grad-CAM..."):
                try:
                    session_id = get_session_id()
                    dataset_config = get_dataset_config_from_file(session_id)
                    transform = create_val_transforms(dataset_config)

                    img = Image.open(selected_sample["path"]).convert("RGB")
                    img_tensor = transform(img)

                    heatmap, _, _ = compute_gradcam(
                        model, device, img_tensor, target_layer
                    )

                    predictions = get_top_predictions(
                        model, device, img_tensor, class_names, top_k=5
                    )

                    st.session_state["gradcam_heatmap"] = heatmap
                    st.session_state["gradcam_img"] = img
                    st.session_state["gradcam_tensor"] = img_tensor
                    st.session_state["gradcam_preds"] = predictions
                    st.session_state["gradcam_true_class"] = selected_sample["class_name"]

                except Exception as e:
                    st.error(f"Grad-CAM failed: {e}")
                    import traceback
                    st.code(traceback.format_exc())

        if "gradcam_heatmap" not in st.session_state:
            return

        heatmap = st.session_state["gradcam_heatmap"]
        img = st.session_state["gradcam_img"]
        predictions = st.session_state["gradcam_preds"]
        true_class = st.session_state["gradcam_true_class"]

        img_resized = img.resize((224, 224))
        overlay = _create_gradcam_overlay(img_resized, heatmap, opacity)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Original")
            st.image(img_resized, width="stretch")

        with col2:
            st.subheader("Heatmap", help=GRADCAM_TOOLTIPS["heatmap"])
            heatmap_colored = plt.cm.jet(heatmap)[:, :, :3]
            st.image(heatmap_colored, width="stretch")

        with col3:
            st.subheader("Overlay")
            st.image(overlay, width="stretch")

        st.divider()
        st.subheader("Predictions")
        st.caption(f"True class: **{true_class}**")

        pred_df = pd.DataFrame([
            {"Class": p["class_name"], "Confidence": f"{p['confidence'] * 100:.1f}%"}
            for p in predictions
        ])
        st.dataframe(pred_df, width="stretch", hide_index=True)

    except Exception as e:
        st.error(f"Failed to load model: {e}")


def _create_gradcam_overlay(
    img: Image.Image, heatmap: np.ndarray, opacity: float
) -> Image.Image:
    """Create Grad-CAM overlay image."""
    heatmap_resized = np.array(
        Image.fromarray((heatmap * 255).astype(np.uint8)).resize(img.size)
    )

    heatmap_colored = plt.cm.jet(heatmap_resized / 255.0)[:, :, :3] * 255

    img_array = np.array(img).astype(np.float32)
    overlay = (1 - opacity) * img_array + opacity * heatmap_colored

    return Image.fromarray(overlay.astype(np.uint8))
