"""
Advanced Charts Module
Confusion matrix, per-class metrics, and classification report visualizations
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_confusion_matrix(test_results: dict, key: str):
    """Render interactive confusion matrix heatmap."""
    cm = test_results.get("confusion_matrix", [])
    class_names = test_results.get("class_names", [])

    if not cm:
        st.warning("No confusion matrix data available.")
        return

    # For large matrices, show a subset or use different visualization
    num_classes = len(class_names)

    if num_classes > 20:
        st.caption(f"Showing {num_classes}x{num_classes} confusion matrix (scroll to explore)")

    fig = go.Figure(data=go.Heatmap(
        z=cm,
        x=class_names,
        y=class_names,
        colorscale="Blues",
        hoverongaps=False,
        hovertemplate="Actual: %{y}<br>Predicted: %{x}<br>Count: %{z}<extra></extra>",
    ))

    fig.update_layout(
        xaxis_title="Predicted",
        yaxis_title="Actual",
        xaxis=dict(tickangle=45, tickfont=dict(size=10 if num_classes > 15 else 12)),
        yaxis=dict(tickfont=dict(size=10 if num_classes > 15 else 12)),
        height=max(400, num_classes * 15),
        margin=dict(l=100, r=20, t=30, b=100),
    )

    st.plotly_chart(fig, width="stretch", key=f"cm_{key}")


def render_per_class_metrics(test_results: dict, key: str):
    """Render per-class precision/recall/F1 bar chart."""
    per_class = test_results.get("per_class", {})
    class_names = test_results.get("class_names", [])

    if not per_class or not class_names:
        st.warning("No per-class metrics available.")
        return

    precision = per_class.get("precision", [])
    recall = per_class.get("recall", [])
    f1 = per_class.get("f1", [])

    # Create dataframe
    df = pd.DataFrame({
        "Class": class_names * 3,
        "Score": [p * 100 for p in precision] + [r * 100 for r in recall] + [f * 100 for f in f1],
        "Metric": ["Precision"] * len(class_names) + ["Recall"] * len(class_names) + ["F1"] * len(class_names),
    })

    # Sort by F1 score for better visualization
    f1_order = sorted(range(len(f1)), key=lambda i: f1[i], reverse=True)
    class_order = [class_names[i] for i in f1_order]

    fig = px.bar(
        df,
        x="Score",
        y="Class",
        color="Metric",
        barmode="group",
        orientation="h",
        color_discrete_map={
            "Precision": "#00CC96",
            "Recall": "#AB63FA",
            "F1": "#FFA15A",
        },
        category_orders={"Class": class_order},
    )

    fig.update_layout(
        xaxis_title="Score (%)",
        yaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=max(400, len(class_names) * 25),
        margin=dict(l=150, r=20, t=40, b=40),
    )

    st.plotly_chart(fig, width="stretch", key=f"pcm_{key}")


def render_classification_table(test_results: dict):
    """Render classification report as styled dataframe."""
    report = test_results.get("classification_report", {})
    class_names = test_results.get("class_names", [])

    if not report:
        st.warning("No classification report available.")
        return

    # Build table data
    rows = []
    for class_name in class_names:
        if class_name in report:
            metrics = report[class_name]
            rows.append({
                "Class": class_name,
                "Precision": f"{metrics['precision']*100:.1f}%",
                "Recall": f"{metrics['recall']*100:.1f}%",
                "F1-Score": f"{metrics['f1-score']*100:.1f}%",
                "Support": int(metrics["support"]),
            })

    # Add summary rows
    for key in ["macro avg", "weighted avg"]:
        if key in report:
            metrics = report[key]
            rows.append({
                "Class": key.title(),
                "Precision": f"{metrics['precision']*100:.1f}%",
                "Recall": f"{metrics['recall']*100:.1f}%",
                "F1-Score": f"{metrics['f1-score']*100:.1f}%",
                "Support": int(metrics["support"]),
            })

    df = pd.DataFrame(rows)

    # Display with styling
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        height=min(400, (len(rows) + 1) * 35 + 40),
    )


def render_accuracy_summary(test_results: dict):
    """Render overall accuracy and sample count."""
    accuracy = test_results.get("accuracy", 0)
    total_samples = test_results.get("total_samples", 0)
    report = test_results.get("classification_report", {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Test Accuracy", f"{accuracy*100:.2f}%")

    with col2:
        st.metric("Test Samples", f"{total_samples:,}")

    with col3:
        macro_f1 = report.get("macro avg", {}).get("f1-score", 0)
        st.metric("Macro F1", f"{macro_f1*100:.2f}%")

    with col4:
        weighted_f1 = report.get("weighted avg", {}).get("f1-score", 0)
        st.metric("Weighted F1", f"{weighted_f1*100:.2f}%")
