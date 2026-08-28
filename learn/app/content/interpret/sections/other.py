"""Other sections (Activation Maps, Filters) for interpretability page."""

from content.interpret.engine.activations import (
    get_activation_maps,
    get_filter_weights,
    normalize_filter_for_display,
)
from content.interpret.engine.data_loader import get_test_samples
from content.interpret.engine.gradcam import get_conv_layers
from content.interpret.engine.model_loader import load_experiment_model
from content.interpret.sections.lime import render_lime_section
from content.interpret.tooltips import ACTIVATION_TOOLTIPS, FILTER_TOOLTIPS
from PIL import Image
from state.persistence import get_dataset_config_from_file
from state.workflow import get_session_id
import streamlit as st
import torch
from training.transforms import create_val_transforms


def render_other_sections(exp_id: str):
    """Render LIME, activation maps, and filter weights sections."""
    section = st.segmented_control(
        "Select Section",
        options=["LIME", "Activation Maps", "Learned Filters"],
        default="LIME",
        key="other_section_select",
    )

    if section == "LIME":
        render_lime_section(exp_id)
    elif section == "Activation Maps":
        render_activation_maps_section(exp_id)
    else:
        render_filter_weights_section(exp_id)


def render_activation_maps_section(exp_id: str):
    """Render activation maps visualization."""
    st.header("Activation Maps", help=ACTIVATION_TOOLTIPS["method"])

    try:
        model, device, _ = load_experiment_model(exp_id)
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
                key="actmap_sample",
            )
            selected_sample = sample_options[selected_sample_name]

        with col2:
            selected_layer_name = st.selectbox(
                "Select Layer",
                options=layer_names,
                key="actmap_layer",
                help=ACTIVATION_TOOLTIPS["layer_selection"],
            )
            target_layer = dict(conv_layers)[selected_layer_name]

        max_filters = st.slider(
            "Max Filters to Show", 8, 64, 32, step=8,
            key="actmap_max",
            help=ACTIVATION_TOOLTIPS["max_filters"],
        )

        if st.button("Generate Activation Maps", key="actmap_run"):
            with st.spinner("Computing activations..."):
                try:
                    session_id = get_session_id()
                    dataset_config = get_dataset_config_from_file(session_id)
                    transform = create_val_transforms(dataset_config)

                    img = Image.open(selected_sample["path"]).convert("RGB")
                    img_tensor = transform(img)

                    activations = get_activation_maps(
                        model, device, img_tensor, target_layer
                    )

                    st.session_state["actmap_data"] = activations
                    st.session_state["actmap_img"] = img

                except Exception as e:
                    st.error(f"Failed: {e}")

        _display_activation_maps(max_filters)

    except Exception as e:
        st.error(f"Failed to load model: {e}")


def _display_activation_maps(max_filters: int):
    """Display activation maps from session state."""
    if "actmap_data" not in st.session_state:
        return

    activations = st.session_state["actmap_data"]
    orig_img = st.session_state["actmap_img"]

    st.divider()
    st.subheader("Original Image")
    st.image(orig_img.resize((224, 224)), width=224)

    st.subheader(f"Activation Maps ({activations.shape[0]} filters)")

    num_filters = min(max_filters, activations.shape[0])
    cols_per_row = 8
    rows = (num_filters + cols_per_row - 1) // cols_per_row

    for row_idx in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx, col in enumerate(cols):
            filter_idx = row_idx * cols_per_row + col_idx
            if filter_idx >= num_filters:
                break

            with col:
                act_map = activations[filter_idx]
                act_map = (act_map - act_map.min()) / (act_map.max() - act_map.min() + 1e-8)
                st.image(act_map, caption=f"F{filter_idx}", width="stretch")


def render_filter_weights_section(exp_id: str):
    """Render learned filter weights visualization."""
    st.header("Learned Filters", help=FILTER_TOOLTIPS["method"])

    try:
        model, _, _ = load_experiment_model(exp_id)
        conv_layers = get_conv_layers(model)

        if not conv_layers:
            st.warning("No convolutional layers found")
            return

        layer_names = [name for name, _ in conv_layers]

        selected_layer_name = st.selectbox(
            "Select Layer",
            options=layer_names,
            key="filter_layer_select",
        )
        target_layer = dict(conv_layers)[selected_layer_name]

        max_filters = st.slider(
            "Max Filters to Show", 8, 64, 32, step=8, key="filter_max"
        )

        if st.button("Show Filter Weights", key="filter_run"):
            with st.spinner("Loading filters..."):
                if hasattr(target_layer, "weight"):
                    conv_layer = target_layer
                else:
                    conv_layer = None
                    for m in target_layer.modules():
                        if isinstance(m, torch.nn.Conv2d):
                            conv_layer = m
                            break

                if conv_layer is None:
                    st.error("Could not find Conv2d layer")
                    return

                weights = get_filter_weights(conv_layer)
                if weights is None:
                    st.error("Failed to get filter weights")
                    return

                st.session_state["filter_weights"] = weights

        _display_filter_weights(max_filters)

    except Exception as e:
        st.error(f"Failed: {e}")


def _display_filter_weights(max_filters: int):
    """Display filter weights from session state."""
    if "filter_weights" not in st.session_state:
        return

    weights = st.session_state["filter_weights"]

    st.divider()
    out_channels, in_channels, kh, kw = weights.shape
    st.caption(
        f"Shape: {out_channels} filters × {in_channels} input channels × {kh}×{kw} kernel"
    )

    num_filters = min(max_filters, out_channels)
    cols_per_row = 8
    rows = (num_filters + cols_per_row - 1) // cols_per_row

    for row_idx in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx, col in enumerate(cols):
            filter_idx = row_idx * cols_per_row + col_idx
            if filter_idx >= num_filters:
                break

            with col:
                filter_w = weights[filter_idx]

                if in_channels == 3:
                    filter_img = filter_w.transpose(1, 2, 0)
                    filter_img = normalize_filter_for_display(filter_img)
                else:
                    filter_img = filter_w.mean(axis=0)
                    filter_img = normalize_filter_for_display(filter_img)

                st.image(
                    filter_img,
                    caption=f"F{filter_idx}",
                    width="stretch",
                )
