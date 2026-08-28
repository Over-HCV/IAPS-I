"""
Results Charts Module
All chart rendering functions for experiment results visualization
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Color palette for consistent styling
COLORS = {
    "train": "#636EFA",
    "val": "#EF553B",
    "precision": "#00CC96",
    "recall": "#AB63FA",
    "f1": "#FFA15A",
    "lr": "#19D3F3",
    "gap": "#FF6692",
}


def render_loss_chart(history: dict, key: str):
    """Render train vs validation loss curves."""
    train_loss = history.get("train_loss", [])
    val_loss = history.get("val_loss", [])

    if not train_loss:
        st.info("No loss data available.")
        return

    epochs = list(range(1, len(train_loss) + 1))

    df = pd.DataFrame(
        {
            "Epoch": epochs * 2,
            "Loss": train_loss + val_loss,
            "Type": ["Train"] * len(train_loss) + ["Validation"] * len(val_loss),
        }
    )

    fig = px.line(
        df,
        x="Epoch",
        y="Loss",
        color="Type",
        color_discrete_map={"Train": COLORS["train"], "Validation": COLORS["val"]},
    )
    fig.update_layout(
        margin=dict(t=30, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    st.plotly_chart(fig, width="stretch", key=f"loss_{key}")


def render_accuracy_chart(history: dict, key: str):
    """Render train vs validation accuracy curves."""
    train_acc = history.get("train_acc", [])
    val_acc = history.get("val_acc", [])

    if not train_acc:
        st.info("No accuracy data available.")
        return

    epochs = list(range(1, len(train_acc) + 1))

    # Convert to percentages
    train_acc_pct = [acc * 100 for acc in train_acc]
    val_acc_pct = [acc * 100 for acc in val_acc]

    df = pd.DataFrame(
        {
            "Epoch": epochs * 2,
            "Accuracy (%)": train_acc_pct + val_acc_pct,
            "Type": ["Train"] * len(train_acc_pct) + ["Validation"] * len(val_acc_pct),
        }
    )

    fig = px.line(
        df,
        x="Epoch",
        y="Accuracy (%)",
        color="Type",
        color_discrete_map={"Train": COLORS["train"], "Validation": COLORS["val"]},
    )
    fig.update_layout(
        margin=dict(t=30, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    st.plotly_chart(fig, width="stretch", key=f"acc_{key}")


def render_prf_chart(history: dict, key: str):
    """Render Precision/Recall/F1 curves (validation)."""
    val_precision = history.get("val_precision", [])
    val_recall = history.get("val_recall", [])
    val_f1 = history.get("val_f1", [])

    if not val_precision:
        st.info("No precision/recall/F1 data available.")
        return

    epochs = list(range(1, len(val_precision) + 1))

    # Convert to percentages
    precision_pct = [v * 100 for v in val_precision]
    recall_pct = [v * 100 for v in val_recall]
    f1_pct = [v * 100 for v in val_f1]

    df = pd.DataFrame(
        {
            "Epoch": epochs * 3,
            "Score (%)": precision_pct + recall_pct + f1_pct,
            "Metric": (
                ["Precision"] * len(precision_pct)
                + ["Recall"] * len(recall_pct)
                + ["F1"] * len(f1_pct)
            ),
        }
    )

    fig = px.line(
        df,
        x="Epoch",
        y="Score (%)",
        color="Metric",
        color_discrete_map={
            "Precision": COLORS["precision"],
            "Recall": COLORS["recall"],
            "F1": COLORS["f1"],
        },
    )
    fig.update_layout(
        margin=dict(t=30, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    st.plotly_chart(fig, width="stretch", key=f"prf_{key}")


def render_lr_chart(history: dict, key: str):
    """Render learning rate schedule."""
    lr_history = history.get("lr", [])

    if not lr_history:
        st.info("No learning rate data available.")
        return

    epochs = list(range(1, len(lr_history) + 1))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=epochs,
            y=lr_history,
            mode="lines+markers",
            line=dict(color=COLORS["lr"]),
            marker=dict(size=6),
            name="Learning Rate",
        )
    )

    fig.update_layout(
        margin=dict(t=30, b=30),
        xaxis_title="Epoch",
        yaxis_title="Learning Rate",
        hovermode="x unified",
        showlegend=False,
    )

    st.plotly_chart(fig, width="stretch", key=f"lr_{key}")


def render_overfitting_gap_chart(history: dict, key: str):
    """Render overfitting gap (train_acc - val_acc) over epochs."""
    train_acc = history.get("train_acc", [])
    val_acc = history.get("val_acc", [])

    if not train_acc or not val_acc:
        st.info("No accuracy data available for gap analysis.")
        return

    epochs = list(range(1, len(train_acc) + 1))

    # Calculate gap (positive = overfitting)
    gap = [(t - v) * 100 for t, v in zip(train_acc, val_acc)]

    fig = go.Figure()

    # Add area fill for visual clarity
    fig.add_trace(
        go.Scatter(
            x=epochs,
            y=gap,
            mode="lines",
            fill="tozeroy",
            line=dict(color=COLORS["gap"]),
            fillcolor="rgba(255, 102, 146, 0.3)",
            name="Overfitting Gap",
        )
    )

    # Add zero reference line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    fig.update_layout(
        margin=dict(t=30, b=30),
        xaxis_title="Epoch",
        yaxis_title="Gap (Train - Val %)",
        hovermode="x unified",
        showlegend=False,
    )

    st.plotly_chart(fig, width="stretch", key=f"gap_{key}")


def render_train_val_f1_comparison(history: dict, key: str):
    """Render train vs validation F1 comparison."""
    train_f1 = history.get("train_f1", [])
    val_f1 = history.get("val_f1", [])

    if not train_f1 or not val_f1:
        st.info("No F1 data available for comparison.")
        return

    epochs = list(range(1, len(train_f1) + 1))

    # Convert to percentages
    train_f1_pct = [f * 100 for f in train_f1]
    val_f1_pct = [f * 100 for f in val_f1]

    df = pd.DataFrame(
        {
            "Epoch": epochs * 2,
            "F1 Score (%)": train_f1_pct + val_f1_pct,
            "Type": ["Train"] * len(train_f1_pct) + ["Validation"] * len(val_f1_pct),
        }
    )

    fig = px.line(
        df,
        x="Epoch",
        y="F1 Score (%)",
        color="Type",
        color_discrete_map={"Train": COLORS["train"], "Validation": COLORS["val"]},
    )
    fig.update_layout(
        margin=dict(t=30, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    st.plotly_chart(fig, width="stretch", key=f"f1cmp_{key}")
