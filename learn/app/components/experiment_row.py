"""
Experiment Row Component
Reusable row for displaying and managing experiments in Monitor page
"""

import streamlit as st

# Status icons and colors
STATUS_CONFIG = {
    "ready": {"icon": "⚪", "label": "Ready", "color": "gray"},
    "training": {"icon": "🔄", "label": "Training", "color": "blue"},
    "paused": {"icon": "⏸️", "label": "Paused", "color": "orange"},
    "completed": {"icon": "✅", "label": "Completed", "color": "green"},
    "failed": {"icon": "❌", "label": "Failed", "color": "red"},
}


def render_experiment_row(
    experiment: dict,
    models: list[dict],
    trainings: list[dict],
    on_update: callable = None,
    on_delete: callable = None,
    on_start: callable = None,
    on_pause: callable = None,
    on_stop: callable = None,
    on_view_results: callable = None,
):
    """
    Render a single experiment row.

    Args:
        experiment: Experiment dict with id, name, model_id, training_id, status, metrics
        models: List of available model configs
        trainings: List of available training configs
        on_update: Callback when experiment config changes
        on_delete: Callback to delete experiment
        on_start: Callback to start training
        on_pause: Callback to pause training
        on_stop: Callback to stop training
        on_view_results: Callback to view results
    """
    exp_id = experiment["id"]
    status = experiment.get("status", "ready")
    status_cfg = STATUS_CONFIG.get(status, STATUS_CONFIG["ready"])

    with st.container(border=True):
        # Row 1: Name and status
        col_name, col_status = st.columns([3, 1])

        with col_name:
            st.markdown(f"**{experiment.get('name', 'Experiment')}**")

        with col_status:
            st.markdown(f"{status_cfg['icon']} {status_cfg['label']}")

        # Row 2: Show config info for non-ready statuses (read-only)
        if status != "ready":
            model_name = next(
                (m["name"] for m in models if m["id"] == experiment.get("model_id")),
                "Unknown Model",
            )
            training_name = next(
                (t["name"] for t in trainings if t["id"] == experiment.get("training_id")),
                "Unknown Config",
            )
            st.caption(f"**Model:** {model_name} | **Training:** {training_name}")

        # Row 2: Model and Training dropdowns (only if ready)
        if status == "ready":
            col_model, col_training = st.columns(2)

            model_options = {m["id"]: m["name"] for m in models}
            training_options = {t["id"]: t["name"] for t in trainings}

            with col_model:
                current_model = experiment.get("model_id")
                model_ids = list(model_options.keys())
                model_index = (
                    model_ids.index(current_model) if current_model in model_ids else 0
                )

                new_model = st.selectbox(
                    "Model",
                    options=model_ids,
                    format_func=lambda x: model_options.get(x, "Unknown"),
                    index=model_index if model_ids else 0,
                    key=f"model_{exp_id}",
                    disabled=not model_ids,
                )

            with col_training:
                current_training = experiment.get("training_id")
                training_ids = list(training_options.keys())
                training_index = (
                    training_ids.index(current_training)
                    if current_training in training_ids
                    else 0
                )

                new_training = st.selectbox(
                    "Training Config",
                    options=training_ids,
                    format_func=lambda x: training_options.get(x, "Unknown"),
                    index=training_index if training_ids else 0,
                    key=f"training_{exp_id}",
                    disabled=not training_ids,
                )

            # Update if changed
            if on_update and (new_model != current_model or new_training != current_training):
                on_update(exp_id, {"model_id": new_model, "training_id": new_training})

        # Row 3: Progress and metrics (if training or completed)
        if status == "training":
            current_epoch = experiment.get("current_epoch", 0)
            max_epochs = experiment.get("max_epochs", 100)
            current_batch = experiment.get("current_batch", 0)
            total_batches = experiment.get("total_batches", 0)

            # Epoch progress bar
            epoch_progress = current_epoch / max_epochs if max_epochs > 0 else 0
            st.progress(epoch_progress, text=f"Epoch {current_epoch}/{max_epochs}")

            # Batch progress bar (within current epoch)
            if total_batches > 0:
                batch_progress = current_batch / total_batches
                st.progress(batch_progress, text=f"Batch {current_batch}/{total_batches}")

            metrics = experiment.get("metrics", {})
            prev_metrics = experiment.get("prev_metrics", {})
            if metrics:
                col1, col2, col3, col4 = st.columns(4)

                # Calculate deltas for trend indicators
                train_loss = metrics.get("train_loss", 0)
                train_acc = metrics.get("train_acc", 0)
                val_loss = metrics.get("val_loss", 0)
                val_acc = metrics.get("val_acc", 0)

                prev_train_loss = prev_metrics.get("train_loss")
                prev_train_acc = prev_metrics.get("train_acc")
                prev_val_loss = prev_metrics.get("val_loss")
                prev_val_acc = prev_metrics.get("val_acc")

                with col1:
                    delta = f"{train_loss - prev_train_loss:.4f}" if prev_train_loss is not None else None
                    st.metric("Train Loss", f"{train_loss:.4f}", delta=delta, delta_color="inverse")
                with col2:
                    delta = f"{(train_acc - prev_train_acc)*100:.1f}%" if prev_train_acc is not None else None
                    st.metric("Train Acc", f"{train_acc*100:.1f}%", delta=delta, delta_color="normal")
                with col3:
                    delta = f"{val_loss - prev_val_loss:.4f}" if prev_val_loss is not None else None
                    st.metric("Val Loss", f"{val_loss:.4f}", delta=delta, delta_color="inverse")
                with col4:
                    delta = f"{(val_acc - prev_val_acc)*100:.1f}%" if prev_val_acc is not None else None
                    st.metric("Val Acc", f"{val_acc*100:.1f}%", delta=delta, delta_color="normal")

        elif status == "completed":
            metrics = experiment.get("metrics", {})
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Final Loss", f"{metrics.get('val_loss', 0):.4f}")
            with col2:
                st.metric("Final Accuracy", f"{metrics.get('val_acc', 0)*100:.1f}%")
            with col3:
                best_epoch = experiment.get("best_epoch", "-")
                st.metric("Best Epoch", best_epoch)
            with col4:
                duration = experiment.get("duration", "-")
                st.metric("Duration", duration)

        elif status == "failed":
            st.error("Training failed. Check logs for details.")

        # Row 4: Action buttons
        _render_action_buttons(
            exp_id,
            status,
            models,
            trainings,
            experiment,
            on_start,
            on_pause,
            on_stop,
            on_view_results,
            on_delete,
        )


def _render_action_buttons(
    exp_id,
    status,
    models,
    trainings,
    experiment,
    on_start,
    on_pause,
    on_stop,
    on_view_results,
    on_delete,
):
    """Render action buttons based on status"""
    if status == "ready":
        col1, col2 = st.columns([3, 1])

        can_start = bool(experiment.get("model_id")) and bool(
            experiment.get("training_id")
        )

        with col1:
            if st.button(
                "▶️ START TRAINING",
                key=f"start_{exp_id}",
                type="primary",
                width="stretch",
                disabled=not can_start or not models or not trainings,
            ):
                if on_start:
                    on_start(exp_id)

        with col2:
            if st.button("🗑️", key=f"del_{exp_id}", help="Delete experiment"):
                if on_delete:
                    on_delete(exp_id)

    elif status == "training":
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("⏸️ Pause", key=f"pause_{exp_id}", width="stretch"):
                if on_pause:
                    on_pause(exp_id)

        with col2:
            if st.button("⏹️ Stop", key=f"stop_{exp_id}", width="stretch"):
                if on_stop:
                    on_stop(exp_id)

        with col3:
            st.button("💾 Save", key=f"save_{exp_id}", width="stretch", disabled=True)

    elif status == "paused":
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "▶️ Resume", key=f"resume_{exp_id}", type="primary", width="stretch"
            ):
                if on_start:
                    on_start(exp_id)

        with col2:
            if st.button("⏹️ Stop", key=f"stop_{exp_id}", width="stretch"):
                if on_stop:
                    on_stop(exp_id)

    elif status == "completed":
        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button(
                "📊 View Results",
                key=f"results_{exp_id}",
                type="primary",
                width="stretch",
            ):
                if on_view_results:
                    on_view_results(exp_id)

        with col2:
            if st.button("🗑️", key=f"del_{exp_id}", help="Delete experiment"):
                if on_delete:
                    on_delete(exp_id)

    elif status == "failed":
        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button(
                "🔄 Retry", key=f"retry_{exp_id}", width="stretch"
            ):
                if on_start:
                    on_start(exp_id)

        with col2:
            if st.button("🗑️", key=f"del_{exp_id}", help="Delete experiment"):
                if on_delete:
                    on_delete(exp_id)
