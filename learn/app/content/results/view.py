"""
Results & Evaluation Page
Display training results with expandable cards per experiment
"""

import pandas as pd
import streamlit as st

from content.results.tooltips import (
    METRICS_TOOLTIPS,
    CONFUSION_MATRIX_TOOLTIPS,
    HISTORY_TOOLTIPS,
    EXPORT_TOOLTIPS,
)
from content.results.advanced_charts import (
    render_accuracy_summary,
    render_classification_table,
    render_confusion_matrix,
    render_per_class_metrics,
)
from content.results.charts import (
    render_accuracy_chart,
    render_loss_chart,
    render_lr_chart,
    render_overfitting_gap_chart,
    render_prf_chart,
    render_train_val_f1_comparison,
)
from state.persistence import get_dataset_config_from_file, get_model_from_file
from state.workflow import (
    get_experiments,
    get_model_from_library,
    get_session_id,
    get_training_from_library,
    update_experiment,
)


def render():
    """Main render function for Results page."""
    st.title("Results & Evaluation", help="View and analyze completed training experiments.")

    # Get completed experiments (most recent first)
    experiments = get_experiments()
    completed = [exp for exp in experiments if exp.get("status") == "completed"]
    completed = list(reversed(completed))

    if not completed:
        st.info("No completed experiments yet. Train a model first.")
        return

    st.caption(f"{len(completed)} completed experiment(s)")

    # Render each experiment as an expander
    for exp in completed:
        _render_experiment_card(exp)


def _render_experiment_card(experiment: dict):
    """Render a single experiment as an expandable card."""
    exp_name = experiment.get("name", experiment["id"])
    model_entry = get_model_from_library(experiment.get("model_id"))
    model_name = model_entry.get("name", "Unknown") if model_entry else "Unknown"

    # Expander label with key metrics
    metrics = experiment.get("metrics", {})
    val_acc = metrics.get("val_acc", 0) * 100

    label = f"{exp_name} | {model_name} | Val Acc: {val_acc:.1f}%"

    with st.expander(label, expanded=False):
        _render_summary_row(experiment, model_entry)
        _render_metrics_row(experiment)

        # Tabs for different chart sections
        tab_curves, tab_advanced = st.tabs(["Training Curves", "Advanced Metrics"])

        with tab_curves:
            _render_training_curves(experiment)

        with tab_advanced:
            _render_advanced_metrics(experiment)


def _render_summary_row(experiment: dict, model_entry: dict | None):
    """Render experiment summary info."""
    training_entry = get_training_from_library(experiment.get("training_id"))

    model_name = model_entry.get("name", "Unknown") if model_entry else "Unknown"
    model_type = model_entry.get("model_type", "") if model_entry else ""
    training_name = training_entry.get("name", "Unknown") if training_entry else "Unknown"

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Model", model_name)
        st.caption(f"Type: {model_type}")

    with col2:
        st.metric("Training Config", training_name)
        epochs = experiment.get("current_epoch", 0)
        st.caption(f"Epochs: {epochs}")

    with col3:
        st.metric("Duration", experiment.get("duration", "N/A"))
        best = experiment.get("best_epoch", "N/A")
        st.caption(f"Best Epoch: {best}")


def _render_metrics_row(experiment: dict):
    """Render final metrics as metric cards."""
    metrics = experiment.get("metrics", {})

    cols = st.columns(5)

    with cols[0]:
        val = metrics.get("val_loss", 0)
        st.metric("Val Loss", f"{val:.4f}", help=HISTORY_TOOLTIPS["loss_curve"])

    with cols[1]:
        val = metrics.get("val_acc", 0) * 100
        st.metric("Val Accuracy", f"{val:.1f}%", help=METRICS_TOOLTIPS["accuracy"])

    with cols[2]:
        val = metrics.get("val_precision", 0) if "val_precision" in metrics else None
        st.metric("Val Precision", f"{val*100:.1f}%" if val else "N/A", help=METRICS_TOOLTIPS["precision"])

    with cols[3]:
        val = metrics.get("val_recall", 0) if "val_recall" in metrics else None
        st.metric("Val Recall", f"{val*100:.1f}%" if val else "N/A", help=METRICS_TOOLTIPS["recall"])

    with cols[4]:
        val = metrics.get("val_f1", 0) if "val_f1" in metrics else None
        st.metric("Val F1", f"{val*100:.1f}%" if val else "N/A", help=METRICS_TOOLTIPS["f1_score"])


def _render_training_curves(experiment: dict):
    """Render training curves tab content."""
    exp_id = experiment["id"]
    history = experiment.get("history", {})

    if not history:
        st.warning("No training history available for this experiment.")
        _render_export_section(experiment)
        return

    # Row 1: Core metrics
    st.markdown("##### Core Training Metrics")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Loss**")
        render_loss_chart(history, exp_id)

    with col2:
        st.markdown("**Accuracy**")
        render_accuracy_chart(history, exp_id)

    with col3:
        st.markdown("**Precision / Recall / F1**")
        render_prf_chart(history, exp_id)

    st.caption("Loss and accuracy curves show convergence. P/R/F1 tracks classification quality per epoch.")

    # Row 2: Learning dynamics
    st.markdown("##### Learning Dynamics")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Learning Rate**")
        render_lr_chart(history, exp_id)

    with col2:
        st.markdown("**Overfitting Gap**")
        render_overfitting_gap_chart(history, exp_id)

    with col3:
        st.markdown("**Train vs Val F1**")
        render_train_val_f1_comparison(history, exp_id)

    st.caption("Learning rate schedule, generalization gap (+ = overfitting), and F1 comparison across splits.")

    _render_export_section(experiment)


def _render_advanced_metrics(experiment: dict):
    """Render advanced metrics - runs test evaluation if needed."""
    exp_id = experiment["id"]

    # Check if test results already exist
    test_results = experiment.get("test_results")

    if not test_results:
        # Run evaluation automatically
        with st.spinner("Running test set evaluation... This may take a moment."):
            try:
                from training.evaluator import run_test_evaluation

                session_id = get_session_id()
                model_entry = get_model_from_file(session_id, experiment.get("model_id"))
                dataset_config = get_dataset_config_from_file(session_id)

                if not model_entry:
                    st.error("Model configuration not found.")
                    return

                test_results = run_test_evaluation(
                    exp_id,
                    model_entry.get("config", {}),
                    dataset_config,
                )

                # Save results to experiment for caching
                update_experiment(exp_id, {"test_results": test_results})
                st.rerun()

            except Exception as e:
                st.error(f"Evaluation failed: {e}")
                import traceback
                st.code(traceback.format_exc())
                return

    # Display test results
    st.markdown("##### Test Set Performance")
    render_accuracy_summary(test_results)

    st.markdown("---")

    # Two columns: confusion matrix and per-class metrics
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Confusion Matrix", help=CONFUSION_MATRIX_TOOLTIPS["matrix"])
        render_confusion_matrix(test_results, exp_id)

    with col2:
        st.markdown("##### Per-Class Metrics", help=METRICS_TOOLTIPS["macro_avg"])
        render_per_class_metrics(test_results, exp_id)

    st.markdown("---")
    st.markdown("##### Classification Report")
    render_classification_table(test_results)


def _render_export_section(experiment: dict):
    """Render export buttons."""
    exp_id = experiment["id"]
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        history = experiment.get("history", {})
        if history:
            df = pd.DataFrame(history)
            csv = df.to_csv(index=False)
            st.download_button(
                "Download Training History (CSV)",
                data=csv,
                file_name=f"{exp_id}_history.csv",
                mime="text/csv",
                key=f"download_history_{exp_id}",
                help=EXPORT_TOOLTIPS["export_report"],
            )
        else:
            st.button("Download Training History (CSV)", disabled=True, key=f"download_history_{exp_id}")

    with col2:
        st.button("Download Model (.pt)", disabled=True, help=EXPORT_TOOLTIPS["export_model"], key=f"download_model_{exp_id}")
