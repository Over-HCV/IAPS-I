"""
Dataset Configuration - Section Renderers
Extracted to keep main view file under 300 lines
"""

from pathlib import Path
import random

from PIL import Image
import plotly.graph_objects as go
import streamlit as st
from utils.dataset_utils import DATASET_ROOT, calculate_split_percentages


def render_class_distribution(dataset_info):
    """Section 3: Show class distribution"""
    st.header("Class Distribution")

    if not dataset_info["train_samples"]:
        st.warning("No training data found")
        return

    classes = sorted(dataset_info["train_samples"].keys())
    train_counts = [dataset_info["train_samples"].get(c, 0) for c in classes]
    val_counts = [dataset_info["val_samples"].get(c, 0) for c in classes]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(name="Training", x=classes, y=train_counts, marker_color="#98c127")
    )
    fig.add_trace(
        go.Bar(name="Validation", x=classes, y=val_counts, marker_color="#8fd7d7")
    )

    fig.update_layout(
        title="Samples per Malware Family",
        xaxis_title="Malware Family",
        yaxis_title="Number of Samples",
        barmode="group",
        height=500,
        xaxis={"tickangle": -45},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#fafafa"},
    )

    st.plotly_chart(fig, width="stretch")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Most Common Classes")
        top_5 = sorted(
            dataset_info["train_samples"].items(), key=lambda x: x[1], reverse=True
        )[:5]
        for cls, count in top_5:
            st.text(f"{cls}: {count:,} samples")

    with col2:
        st.subheader("Least Common Classes")
        bottom_5 = sorted(dataset_info["train_samples"].items(), key=lambda x: x[1])[:5]
        for cls, count in bottom_5:
            st.text(f"{cls}: {count:,} samples")


def render_sample_visualization(dataset_info):
    """Section 4: Preview dataset images with dimensions"""
    st.header("Dataset Preview")

    if not dataset_info["sample_paths"]:
        st.warning("No sample images found")
        return

    selected_class = st.selectbox(
        "Filter by Malware Family", options=["All"] + dataset_info["classes"]
    )

    if selected_class == "All":
        all_samples = []
        for paths in dataset_info["sample_paths"].values():
            all_samples.extend(paths[:2])
        sample_paths = random.sample(all_samples, min(10, len(all_samples)))
    else:
        sample_paths = dataset_info["sample_paths"].get(selected_class, [])[:8]

    if not sample_paths:
        st.info("No samples available for this class")
        return

    cols = st.columns(5)
    for idx, img_path in enumerate(sample_paths):
        with cols[idx % 5]:
            try:
                img = Image.open(img_path)
                st.image(img, width="stretch")
                st.caption(f"{img.size[0]}x{img.size[1]}")
            except Exception as exception:
                st.error(f"Error loading image: {exception}.\n{img_path.name}")


def render_preprocessing(dataset_info):
    """Section 5: Image preprocessing config"""
    st.header("Image Preprocessing")

    col1, col2, col3 = st.columns(3)
    with col1:
        target_size = st.selectbox(
            "Target Size", ["224x224", "256x256", "299x299", "512x512"], index=0
        )
    with col2:
        normalization = st.radio(
            "Normalization", ["[0,1] Scale", "[-1,1] Scale", "ImageNet Mean/Std"]
        )
        st.info(f"Normalization: {normalization}")
    with col3:
        color_mode = st.radio("Color Mode", ["RGB", "Grayscale"])

    st.subheader("Preprocessing Preview")

    if dataset_info["sample_paths"]:
        sample_class = list(dataset_info["sample_paths"].keys())[0]
        sample_path = dataset_info["sample_paths"][sample_class][0]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Original Image**")
            try:
                original = Image.open(sample_path)
                st.image(original, width="stretch")
                st.caption(f"Size: {original.size[0]}x{original.size[1]}")
            except Exception as e:
                st.error(f"Error loading image: {e}")

        with col2:
            st.markdown("**After Preprocessing**")
            try:
                size = int(target_size.split("x")[0])
                processed = Image.open(sample_path)
                processed = processed.resize((size, size), Image.Resampling.LANCZOS)

                if color_mode == "Grayscale":
                    processed = processed.convert("L")

                st.image(processed, width="stretch")
                st.caption(f"Size: {size}x{size}, Mode: {color_mode}")
            except Exception as e:
                st.error(f"Error processing: {e}")


def render_augmentation():
    """Section 6: Data augmentation config"""
    st.header("Data Augmentation")

    preset = st.radio(
        "Augmentation Preset",
        ["None", "Light", "Moderate", "Heavy", "Custom"],
        horizontal=True,
    )

    preset_info = {
        "None": "No augmentation applied",
        "Light": "Horizontal flip + Small rotation (±10°)",
        "Moderate": "Horizontal/Vertical flip + Rotation (±20°) + Brightness (±10%)",
        "Heavy": "All flips + Rotation (±30°) + Brightness/Contrast (±20%) + Noise",
    }

    if preset != "Custom":
        st.info(preset_info.get(preset, ""))

    if preset == "Custom":
        st.subheader("Custom Augmentation Configuration")

        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Horizontal Flip", value=True)
            st.checkbox("Vertical Flip", value=False)
            rotation = st.checkbox("Random Rotation", value=True)
            if rotation:
                st.slider("Rotation Range (degrees)", 0, 180, 15)

        with col2:
            brightness = st.checkbox("Brightness Adjustment", value=True)
            if brightness:
                st.slider("Brightness Range (%)", 0, 50, 10)

            contrast = st.checkbox("Contrast Adjustment", value=False)
            if contrast:
                st.slider("Contrast Range (%)", 0, 50, 10)

            st.checkbox("Gaussian Noise", value=False)


def render_confirmation():
    """Section 7: Summary and save configuration"""
    st.divider()
    st.header("Configuration Summary")

    train_pct = st.session_state.get("train_split", 70)
    val_of_remaining = st.session_state.get("val_split", 50)
    train_final, val_final, test_final = calculate_split_percentages(
        train_pct, val_of_remaining
    )

    config = {
        "dataset_path": str(DATASET_ROOT.relative_to(Path.cwd())),
        "total_samples": st.session_state.dataset_info["total_train"]
        + st.session_state.dataset_info["total_val"],
        "num_classes": len(st.session_state.dataset_info["classes"]),
        "split": {
            "train": round(train_final, 1),
            "val": round(val_final, 1),
            "test": round(test_final, 1),
        },
    }

    _, col2, _ = st.columns([1, 1, 1])

    with col2:
        if st.button("Save Configuration", type="primary", width="stretch"):
            st.session_state.dataset_config = config
            st.success("Configuration saved!")
            st.balloons()

    if st.session_state.get("dataset_config"):
        st.info("Configuration saved. Navigate to **Model** page to continue.")

    st.json(config)
