"""
Model Card Component
Reusable card for displaying model configurations in the library
"""

from datetime import datetime
import streamlit as st

# Icons by model type
MODEL_ICONS = {
    "Custom CNN": "🔧",
    "Transformer": "🧪",
    "Transfer Learning": "🎯",
}


def render_model_card(
    model: dict,
    on_edit: callable = None,
    on_delete: callable = None,
    is_selected: bool = False,
) -> bool:
    """
    Render a single model card.

    Args:
        model: Model dictionary with id, name, model_type, created_at, config
        on_edit: Callback when edit is clicked (receives model_id)
        on_delete: Callback when delete is clicked (receives model_id)
        is_selected: Whether this card is currently selected

    Returns:
        True if the card was clicked (for selection)
    """
    model_id = model["id"]
    model_type = model.get("model_type", "Unknown")
    icon = MODEL_ICONS.get(model_type, "🧠")

    # Parse creation date
    created_at = model.get("created_at", "")
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at)
            date_str = dt.strftime("%Y-%m-%d")
        except ValueError:
            date_str = created_at[:10]
    else:
        date_str = "Unknown"

    # Get model-specific info for subtitle
    subtitle = _get_model_subtitle(model)

    # Card styling
    border_color = "#4CAF50" if is_selected else "#444"
    border_width = "2px" if is_selected else "1px"

    clicked = False

    with st.container(border=True):
        # Header row: icon + name
        col_icon, col_name = st.columns([1, 5])
        with col_icon:
            st.markdown(f"### {icon}")
        with col_name:
            st.markdown(f"**{model['name']}**")
            st.caption(f"{model_type} • {date_str}")

        # Subtitle with model details
        st.caption(subtitle)

        # Action buttons
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            if st.button("Select", key=f"select_{model_id}", width="stretch"):
                clicked = True

        with col2:
            if on_edit and st.button("✏️", key=f"edit_{model_id}", help="Edit model"):
                on_edit(model_id)

        with col3:
            if on_delete and st.button(
                "🗑️", key=f"del_{model_id}", help="Delete model"
            ):
                on_delete(model_id)

    return clicked


def _get_model_subtitle(model: dict) -> str:
    """Generate subtitle based on model type"""
    config = model.get("config", {})
    model_type = model.get("model_type", "")

    if model_type == "Custom CNN":
        cnn_cfg = config.get("cnn_config", {})
        layers = cnn_cfg.get("layers", [])
        return f"{len(layers)} layers"

    elif model_type == "Transfer Learning":
        transfer_cfg = config.get("transfer_config", {})
        base = transfer_cfg.get("base_model", "Unknown")
        strategy = transfer_cfg.get("strategy", "")
        return f"{base} • {strategy}"

    elif model_type == "Transformer":
        transformer_cfg = config.get("transformer_config", {})
        depth = transformer_cfg.get("depth", 12)
        heads = transformer_cfg.get("num_heads", 12)
        return f"D{depth} H{heads}"

    return ""


def render_model_library(
    models: list[dict],
    selected_id: str | None = None,
    on_select: callable = None,
    on_edit: callable = None,
    on_delete: callable = None,
    cards_per_row: int = 3,
):
    """
    Render the full model library as a grid of cards.

    Args:
        models: List of model dictionaries
        selected_id: Currently selected model ID
        on_select: Callback when a model is selected
        on_edit: Callback when edit is clicked
        on_delete: Callback when delete is clicked
        cards_per_row: Number of cards per row
    """
    if not models:
        st.info("No models saved yet. Create your first model below.")
        return

    # Render in rows
    for i in range(0, len(models), cards_per_row):
        row_models = models[i : i + cards_per_row]
        cols = st.columns(cards_per_row)

        for j, model in enumerate(row_models):
            with cols[j]:
                is_selected = model["id"] == selected_id
                clicked = render_model_card(
                    model,
                    on_edit=on_edit,
                    on_delete=on_delete,
                    is_selected=is_selected,
                )
                if clicked and on_select:
                    on_select(model["id"])
