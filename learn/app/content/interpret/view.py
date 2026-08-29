"""
Model Interpretability Page
Visualizations for understanding model behavior and decisions
"""

import streamlit as st

from content.interpret.engine.model_loader import get_completed_experiments
from content.interpret.sections.architecture import render_architecture_review
from content.interpret.sections.embeddings import render_embeddings
from content.interpret.sections.gradcam import render_gradcam
from content.interpret.sections.importance import render_feature_importance
from content.interpret.sections.misclassifications import render_misclassifications
from content.interpret.sections.other import render_other_sections
from content.interpret.tooltips import TAB_TOOLTIPS
from state.persistence import get_dataset_config_from_file
from state.workflow import get_session_id


def render():
    """Main render function for Interpretability page"""
    st.title("Model Interpretability", help="Visualize and understand how your trained model makes predictions.")

    completed = get_completed_experiments()
    if not completed:
        st.info("No trained model available. Complete training first.")
        return

    exp_options = {f"{exp.get('name', exp['id'])}": exp["id"] for exp in completed}
    selected_name = st.selectbox(
        "Select Experiment",
        options=list(exp_options.keys()),
        key="interpret_experiment",
        help="Choose a completed experiment to analyze.",
    )
    selected_exp_id = exp_options[selected_name]

    st.divider()

    dataset_config = get_dataset_config_from_file(get_session_id())
    if dataset_config.get("dataset_kind") == "tabular":
        _render_tabular_tabs(selected_exp_id)
        return

    _render_image_tabs(selected_exp_id)


def _render_image_tabs(experiment_id: str):
    """Interpretability views for a model trained on images"""
    st.caption(
        f"**Architecture**: {TAB_TOOLTIPS['architecture'][:50]}... | "
        f"**Grad-CAM**: {TAB_TOOLTIPS['gradcam'][:40]}..."
    )

    tab_arch, tab_misclass, tab_embed, tab_gradcam, tab_other = st.tabs(
        [
            "Architecture",
            "Misclassifications",
            "Embeddings",
            "Grad-CAM",
            "Advanced",
        ]
    )

    with tab_arch:
        render_architecture_review(experiment_id)

    with tab_misclass:
        render_misclassifications(experiment_id)

    with tab_embed:
        render_embeddings(experiment_id)

    with tab_gradcam:
        render_gradcam(experiment_id)

    with tab_other:
        render_other_sections(experiment_id)


def _render_tabular_tabs(experiment_id: str):
    """Interpretability views for a model trained on rows.

    Grad-CAM highlights pixels and the embedding view plots image thumbnails;
    neither has a meaning when a sample is a row, so they are replaced by
    permutation importance rather than shown broken.
    """
    tab_arch, tab_importance, tab_misclass = st.tabs(
        ["Architecture", "Feature Importance", "Misclassifications"]
    )

    with tab_arch:
        render_architecture_review(experiment_id)

    with tab_importance:
        render_feature_importance(experiment_id)

    with tab_misclass:
        render_misclassifications(experiment_id)

    st.caption(
        "Grad-CAM and the embedding projector are image-only views and are hidden "
        "for tabular datasets."
    )
