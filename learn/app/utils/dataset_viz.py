"""
Dataset visualization helpers
"""

import random

from PIL import Image
import plotly.graph_objects as go
import streamlit as st


def render_class_distribution_chart(dataset_info):
    """Render Plotly bar chart for class distribution"""
    if not dataset_info["train_samples"]:
        st.warning("No training data found")
        return

    classes = sorted(dataset_info["train_samples"].keys())
    train_counts = [dataset_info["train_samples"].get(c, 0) for c in classes]
    val_counts = [dataset_info["val_samples"].get(c, 0) for c in classes]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Training",
            x=classes,
            y=train_counts,
            marker_color="#98c127",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Validation",
            x=classes,
            y=val_counts,
            marker_color="#8fd7d7",
        )
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


def render_class_summary(dataset_info):
    """Show top and bottom classes by sample count"""
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


def render_sample_grid(dataset_info, selected_class):
    """Display grid of sample images with dimensions"""
    if not dataset_info["sample_paths"]:
        st.warning("No sample images found")
        return

    # Get sample images based on selection
    if selected_class == "All":
        all_samples = []
        for paths in dataset_info["sample_paths"].values():
            all_samples.extend(paths[:2])
        sample_paths = random.sample(all_samples, min(10, len(all_samples)))
    else:
        sample_paths = dataset_info["sample_paths"].get(selected_class, [])[:10]

    if not sample_paths:
        st.info("No samples available for this class")
        return

    # Display in 5-column grid
    cols = st.columns(5)
    for idx, img_path in enumerate(sample_paths):
        with cols[idx % 5]:
            try:
                img = Image.open(img_path)
                st.image(img, width="stretch")
                st.caption(f"{img.size[0]}x{img.size[1]}")
            except Exception as exception:
                st.error(f"Error: {img_path.name}. {exception}")


def render_split_pie_chart(train_final, val_final, test_final):
    """Render pie chart for data split distribution"""
    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Train", "Validation", "Test"],
                values=[train_final, val_final, test_final],
                marker_colors=["#98c127", "#8fd7d7", "#ffb255"],
                hole=0.3,
            )
        ]
    )
    fig.update_layout(
        title="Data Split Distribution",
        height=300,
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width="stretch")


def render_preprocessing_preview(sample_path, target_size, color_mode):
    """Show before/after preprocessing comparison"""
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
