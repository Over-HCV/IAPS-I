"""
Model Interpretability Page
Visualizations for understanding model behavior and decisions
"""

from content.interpret.engine.model_loader import get_completed_experiments
from content.interpret.sections.architecture import render_architecture_review
from content.interpret.sections.embeddings import render_embeddings
from content.interpret.sections.gradcam import render_gradcam
from content.interpret.sections.misclassifications import render_misclassifications
from content.interpret.sections.other import render_other_sections
from content.interpret.tooltips import TAB_TOOLTIPS
import streamlit as st


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

    # Display tab tooltips as caption
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
        render_architecture_review(selected_exp_id)

    with tab_misclass:
        render_misclassifications(selected_exp_id)

    with tab_embed:
        render_embeddings(selected_exp_id)

    with tab_gradcam:
        render_gradcam(selected_exp_id)

    with tab_other:
        render_other_sections(selected_exp_id)
