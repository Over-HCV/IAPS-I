"""Misclassifications section for interpretability page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from content.interpret.engine.data_loader import get_test_dataloader
from content.interpret.engine.misclassifications import (
    get_misclassifications,
    tensor_to_image,
)
from content.interpret.engine.model_loader import load_experiment_model


def render_misclassifications(exp_id: str):
    """Section: Misclassified samples analysis"""
    st.header("Misclassified Samples")

    col1, col2 = st.columns(2)
    with col1:
        n_samples = st.slider("Number of samples", 5, 50, 20, key="misclass_n")
    with col2:
        cols_per_row = st.slider("Columns per row", 2, 6, 4, key="misclass_cols")

    if st.button("Analyze Misclassifications", key="misclass_run"):
        with st.spinner("Loading model and running inference..."):
            try:
                model, device, _ = load_experiment_model(exp_id)
                test_loader, class_names = get_test_dataloader(batch_size=32)

                misclassified = get_misclassifications(
                    model, device, test_loader, class_names, n_samples=n_samples
                )

                if not misclassified:
                    st.success("No misclassifications found in the test set!")
                    return

                st.session_state["misclassified_samples"] = misclassified
                st.session_state["misclass_class_names"] = class_names

            except Exception as e:
                st.error(f"Analysis failed: {e}")
                return

    if "misclassified_samples" not in st.session_state:
        return

    misclassified = st.session_state["misclassified_samples"]

    st.caption(f"Found {len(misclassified)} misclassified samples")

    filter_by = st.selectbox(
        "Filter by",
        ["All", "By True Class", "By Predicted Class"],
        key="misclass_filter",
    )

    if filter_by == "By True Class":
        true_classes = sorted({m["true_class"] for m in misclassified})
        selected_class = st.selectbox(
            "True Class", true_classes, key="misclass_true_class"
        )
        misclassified = [
            m for m in misclassified if m["true_class"] == selected_class
        ]
    elif filter_by == "By Predicted Class":
        pred_classes = sorted({m["pred_class"] for m in misclassified})
        selected_class = st.selectbox(
            "Predicted Class", pred_classes, key="misclass_pred_class"
        )
        misclassified = [
            m for m in misclassified if m["pred_class"] == selected_class
        ]

    with st.expander("Error Distribution"):
        _render_error_distribution(st.session_state["misclassified_samples"])

    _render_misclass_gallery(misclassified, cols_per_row)


def _render_misclass_gallery(samples: list[dict], cols_per_row: int):
    """Render grid of misclassified samples."""
    rows = [samples[i : i + cols_per_row] for i in range(0, len(samples), cols_per_row)]

    for row in rows:
        cols = st.columns(cols_per_row)
        for col, sample in zip(cols, row, strict=False):
            with col:
                img = tensor_to_image(sample["image_tensor"])
                st.image(img, width="stretch")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**True:** {sample['true_class']}")
                with col2:
                    st.markdown(f"**Pred:** {sample['pred_class']}")
                st.caption(f"Conf: {sample['confidence'] * 100:.1f}%")


def _render_error_distribution(samples: list[dict]):
    """Render error distribution chart."""
    transitions = {}
    for s in samples:
        key = f"{s['true_class']} → {s['pred_class']}"
        transitions[key] = transitions.get(key, 0) + 1

    sorted_trans = sorted(transitions.items(), key=lambda x: x[1], reverse=True)[:15]

    if sorted_trans:
        df = pd.DataFrame(sorted_trans, columns=["Transition", "Count"])
        fig = px.bar(df, x="Count", y="Transition", orientation="h")
        fig.update_layout(
            height=max(300, len(sorted_trans) * 25),
            margin={"l": 200, "r": 20, "t": 20, "b": 20},
            yaxis={"autorange": "reversed"},
        )
        st.plotly_chart(fig, width="stretch", key="misclass_dist_chart")
