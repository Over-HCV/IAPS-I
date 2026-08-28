"""Architecture review section for interpretability page."""

import pandas as pd
import streamlit as st

from content.interpret.engine.architecture import (
    get_architecture_summary,
    measure_inference_time,
)
from content.interpret.engine.model_loader import load_experiment_model


def render_architecture_review(exp_id: str):
    """Section: Model architecture summary"""
    st.header("Architecture Summary")

    try:
        model, device, _ = load_experiment_model(exp_id)
        summary = get_architecture_summary(model)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Params", f"{summary['total_params']:,}")

        with col2:
            st.metric("Trainable Params", f"{summary['trainable_params']:,}")

        with col3:
            st.metric("Model Size", f"{summary['model_size_mb']:.1f} MB")

        with col4:
            with st.spinner("Measuring..."):
                inference_time = measure_inference_time(model, device)
            st.metric("Inference Time", f"{inference_time:.1f} ms")

        st.divider()

        st.subheader("Layer Details")

        layers_df = pd.DataFrame(summary["layers"])
        if not layers_df.empty:
            layers_df["trainable"] = layers_df["trainable"].map({True: "✓", False: "✗"})
            layers_df["params"] = layers_df["params"].apply(
                lambda x: f"{x:,}" if x > 0 else "-"
            )
            layers_df.columns = ["Name", "Type", "Shape", "Parameters", "Trainable"]

            st.dataframe(
                layers_df,
                width="stretch",
                hide_index=True,
                height=min(400, len(layers_df) * 35 + 40),
            )
        else:
            st.warning("No layer details available")

        arch_text = _format_architecture_text(summary)
        st.download_button(
            "Download Architecture Summary",
            data=arch_text,
            file_name=f"{exp_id}_architecture.txt",
            mime="text/plain",
            key="arch_download",
        )

    except Exception as e:
        st.error(f"Failed to load model: {e}")


def _format_architecture_text(summary: dict) -> str:
    """Format architecture as text for export."""
    lines = [
        "=" * 60,
        "MODEL ARCHITECTURE SUMMARY",
        "=" * 60,
        "",
        f"Total Parameters: {summary['total_params']:,}",
        f"Trainable Parameters: {summary['trainable_params']:,}",
        f"Model Size: {summary['model_size_mb']:.2f} MB",
        "",
        "-" * 60,
        "LAYERS",
        "-" * 60,
        "",
    ]

    for layer in summary["layers"]:
        trainable = "T" if layer["trainable"] else "F"
        params = f"{layer['params']:,}" if layer["params"] > 0 else "-"
        lines.append(
            f"[{trainable}] {layer['name']}: {layer['type']} {layer['shape']} ({params} params)"
        )

    return "\n".join(lines)
