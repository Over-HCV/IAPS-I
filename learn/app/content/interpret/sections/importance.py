"""
Permutation feature importance for tabular models

Shuffling one feature column and measuring how much accuracy drops says how much
the model actually relied on that column. Model-agnostic, and the only
interpretability view that makes sense when a sample is a row rather than an
image.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import torch

from content.interpret.engine.data_loader import get_test_dataloader
from content.interpret.engine.model_loader import load_experiment_model
from state.persistence import get_dataset_config_from_file
from state.workflow import get_session_id

DEFAULT_REPEATS = 5
MAX_REPEATS = 20


def render_feature_importance(experiment_id: str) -> None:
    """Permutation importance over the test split"""
    st.subheader("Permutation Feature Importance")
    st.caption(
        "Each feature is shuffled in turn; the resulting drop in accuracy is how "
        "much the model depended on it. Higher means more important."
    )

    dataset_config = get_dataset_config_from_file(get_session_id())
    feature_names = _feature_names(dataset_config)

    repeats = st.slider(
        "Shuffles per feature",
        min_value=1,
        max_value=MAX_REPEATS,
        value=DEFAULT_REPEATS,
        key=f"importance_repeats_{experiment_id}",
        help="More shuffles give a steadier estimate and take longer",
    )

    if not st.button("Compute importance", key=f"importance_run_{experiment_id}"):
        return

    with st.spinner("Shuffling features..."):
        try:
            result = _compute_importance(experiment_id, repeats)
        except Exception as exception:
            st.error(f"Could not compute importance: {exception}")
            return

    baseline, importances = result
    _render_results(baseline, importances, feature_names)


def _feature_names(dataset_config: dict) -> list[str]:
    """Configured feature column names, if the config still has them"""
    return list(dataset_config.get("feature_columns", []))


@torch.no_grad()
def _compute_importance(
    experiment_id: str, repeats: int
) -> tuple[float, np.ndarray]:
    """Return (baseline accuracy, mean accuracy drop per feature)"""
    model, device, _ = load_experiment_model(experiment_id)
    test_loader, _ = get_test_dataloader()

    features = []
    targets = []
    for batch_features, batch_targets in test_loader:
        features.append(batch_features)
        targets.append(batch_targets)

    features = torch.cat(features).to(device)
    targets = torch.cat(targets).to(device)

    if features.dim() != 2:
        raise ValueError(
            "Permutation importance needs flat feature rows; this experiment does "
            "not use a tabular dataset."
        )

    baseline = _accuracy(model, features, targets)

    generator = np.random.default_rng(seed=72)
    num_features = features.shape[1]
    drops = np.zeros(num_features)

    for column in range(num_features):
        for _ in range(repeats):
            shuffled = features.clone()
            order = generator.permutation(len(shuffled))
            shuffled[:, column] = shuffled[order, column]
            drops[column] += baseline - _accuracy(model, shuffled, targets)

    return baseline, drops / repeats


def _accuracy(model, features: torch.Tensor, targets: torch.Tensor) -> float:
    """Fraction of correct predictions"""
    predictions = model(features).argmax(dim=1)

    return predictions.eq(targets).float().mean().item()


def _render_results(
    baseline: float, importances: np.ndarray, feature_names: list[str]
) -> None:
    """Bar chart and table of per-feature importance"""
    names = feature_names if len(feature_names) == len(importances) else [
        f"feature {index}" for index in range(len(importances))
    ]

    if len(feature_names) not in (0, len(importances)):
        st.caption(
            "Encoded columns outnumber the original columns (one-hot encoding), "
            "so features are shown by position."
        )

    st.metric("Baseline test accuracy", f"{baseline:.2%}")

    table = pd.DataFrame(
        {"feature": names, "accuracy_drop": importances}
    ).sort_values("accuracy_drop", ascending=False)

    figure = go.Figure(
        go.Bar(
            x=table["accuracy_drop"],
            y=table["feature"],
            orientation="h",
            marker_color="#98c127",
        )
    )
    figure.update_layout(
        title="Accuracy drop when a feature is shuffled",
        xaxis_title="Accuracy drop",
        height=max(300, 28 * len(table)),
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis={"autorange": "reversed"},
    )
    st.plotly_chart(figure, width="stretch")

    st.dataframe(table, width="stretch", hide_index=True)
