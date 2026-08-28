"""Embeddings visualization section for interpretability page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from content.interpret.engine.data_loader import get_test_dataloader
from content.interpret.engine.embeddings import (
    compute_clustering_metrics,
    compute_embeddings,
    extract_features,
)
from content.interpret.engine.model_loader import load_experiment_model
from content.interpret.tooltips import EMBEDDINGS_TOOLTIPS


def render_embeddings(exp_id: str):
    """Section: t-SNE/UMAP/PCA embeddings visualization"""
    st.header("Feature Space Visualization", help="Visualize learned features in 2D. Well-separated clusters indicate good class discrimination.")

    col1, col2 = st.columns(2)

    with col1:
        method = st.selectbox(
            "Method", ["t-SNE", "PCA", "UMAP"],
            key="embed_method",
            help="t-SNE: best for visualization. PCA: fast, linear. UMAP: balance of both.",
        )

    with col2:
        n_samples = st.slider(
            "Max Samples", 100, 1000, 500, step=50,
            key="embed_samples",
            help="Number of test samples to visualize. More = slower but more representative.",
        )

    perplexity = 30
    n_neighbors = 15
    if method == "t-SNE":
        perplexity = st.slider(
            "Perplexity", 5, 50, 30,
            key="embed_perplexity",
            help=EMBEDDINGS_TOOLTIPS["perplexity"],
        )
    elif method == "UMAP":
        n_neighbors = st.slider(
            "N Neighbors", 5, 50, 15,
            key="embed_neighbors",
            help=EMBEDDINGS_TOOLTIPS["n_neighbors"],
        )

    if st.button("Compute Embeddings", key="embed_run"):
        with st.spinner(f"Extracting features and computing {method}..."):
            try:
                model, device, _ = load_experiment_model(exp_id)
                test_loader, class_names = get_test_dataloader(batch_size=32)

                features, labels, predictions = extract_features(
                    model, device, test_loader, max_samples=n_samples
                )

                st.info(
                    f"Extracted {len(features)} samples, {features.shape[1]} features"
                )

                embeddings = compute_embeddings(
                    features,
                    method=method,
                    perplexity=perplexity,
                    n_neighbors=n_neighbors,
                )

                metrics = compute_clustering_metrics(embeddings, labels)

                st.session_state["embeddings"] = embeddings
                st.session_state["embed_labels"] = labels
                st.session_state["embed_preds"] = predictions
                st.session_state["embed_class_names"] = class_names
                st.session_state["embed_metrics"] = metrics
                st.session_state["embed_computed_method"] = method

            except ImportError as e:
                st.error(f"Missing dependency: {e}")
                st.info("For UMAP, install: `pip install umap-learn`")
            except Exception as e:
                st.error(f"Failed to compute embeddings: {e}")
                import traceback
                st.code(traceback.format_exc())

    if "embeddings" not in st.session_state:
        return

    embeddings = st.session_state["embeddings"]
    labels = st.session_state["embed_labels"]
    predictions = st.session_state["embed_preds"]
    class_names = st.session_state["embed_class_names"]
    metrics = st.session_state["embed_metrics"]
    embed_method = st.session_state.get("embed_computed_method", method)

    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Silhouette Score", f"{metrics['silhouette']:.3f}",
            help=EMBEDDINGS_TOOLTIPS["silhouette_score"],
        )
    with col2:
        st.metric(
            "Davies-Bouldin Index", f"{metrics['davies_bouldin']:.3f}",
            help=EMBEDDINGS_TOOLTIPS["davies_bouldin"],
        )

    st.divider()

    col_true, col_correct, col_pred = st.columns(3)

    true_colors = [class_names[label] for label in labels]
    pred_colors = [class_names[pred] for pred in predictions]
    correct_colors = [
        "Correct" if label == pred else "Incorrect"
        for label, pred in zip(labels, predictions, strict=True)
    ]

    with col_true:
        st.subheader("By True Class")
        df_true = pd.DataFrame({
            "x": embeddings[:, 0],
            "y": embeddings[:, 1],
            "Class": true_colors,
        })
        fig_true = px.scatter(df_true, x="x", y="y", color="Class", hover_data=["Class"])
        fig_true.update_layout(
            height=400,
            showlegend=False,
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
            xaxis_title="",
            yaxis_title="",
        )
        st.plotly_chart(fig_true, width="stretch", key="embed_true")

    with col_correct:
        st.subheader("Correct vs Incorrect")
        df_correct = pd.DataFrame({
            "x": embeddings[:, 0],
            "y": embeddings[:, 1],
            "Result": correct_colors,
        })
        fig_correct = px.scatter(
            df_correct,
            x="x",
            y="y",
            color="Result",
            hover_data=["Result"],
            color_discrete_map={"Correct": "#00CC96", "Incorrect": "#EF553B"},
        )
        fig_correct.update_layout(
            height=400,
            showlegend=True,
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
            margin={"l": 20, "r": 20, "t": 40, "b": 20},
            xaxis_title="",
            yaxis_title="",
        )
        st.plotly_chart(fig_correct, width="stretch", key="embed_correct")

    with col_pred:
        st.subheader("By Predicted")
        df_pred = pd.DataFrame({
            "x": embeddings[:, 0],
            "y": embeddings[:, 1],
            "Class": pred_colors,
        })
        fig_pred = px.scatter(df_pred, x="x", y="y", color="Class", hover_data=["Class"])
        fig_pred.update_layout(
            height=400,
            showlegend=False,
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
            xaxis_title="",
            yaxis_title="",
        )
        st.plotly_chart(fig_pred, width="stretch", key="embed_pred")

    n_correct = sum(1 for c in correct_colors if c == "Correct")
    st.caption(
        f"{embed_method}: {n_correct}/{len(correct_colors)} correct "
        f"({100 * n_correct / len(correct_colors):.1f}%)"
    )
