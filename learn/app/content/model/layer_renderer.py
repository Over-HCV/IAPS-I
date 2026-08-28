"""
Layer Renderer - UI components for rendering and editing layers
"""

from content.model.layer_builder import (
    add_layer,
    duplicate_layer,
    get_layer_stack,
    is_editing,
    load_preset,
    move_layer_down,
    move_layer_up,
    remove_layer,
    start_editing,
    stop_editing,
    update_layer,
)
from content.model.layer_configs import (
    LAYER_TYPES,
    PRESETS,
    get_layer_display,
    validate_layer_stack,
)
import streamlit as st


def render_preset_selector():
    """Render preset selector and load button"""
    col1, col2 = st.columns([3, 1])

    with col1:
        preset_options = {k: v["name"] for k, v in PRESETS.items()}
        current_preset = st.session_state.get("selected_preset", "profesor")

        selected = st.selectbox(
            "Architecture Preset",
            options=list(preset_options.keys()),
            format_func=lambda x: preset_options[x],
            index=list(preset_options.keys()).index(current_preset)
            if current_preset in preset_options
            else 0,
            key="preset_selector",
            help="Load a pre-built layer configuration. 'Conventional' is a good starting point. You can customize after loading.",
        )

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("Load Preset", type="secondary", width="stretch"):
            load_preset(selected)
            st.rerun()

    # Show preset description
    if selected in PRESETS:
        st.caption(f"📋 {PRESETS[selected]['description']}")


def render_add_layer_section():
    """Render the section to add new layers"""
    st.subheader("Add Layer")

    col1, col2 = st.columns([3, 1])

    with col1:
        layer_options = {
            k: f"{v['icon']} {v['display_name']}" for k, v in LAYER_TYPES.items()
        }

        selected_type = st.selectbox(
            "Layer Type",
            options=list(layer_options.keys()),
            format_func=lambda x: layer_options[x],
            key="new_layer_type",
            help="Conv2D extracts features. Pooling reduces size. BatchNorm stabilizes training. Dropout prevents overfitting. Dense/Flatten for classification.",
        )

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("+ Add", type="primary", width="stretch"):
            add_layer(selected_type)
            st.rerun()

    # Show layer description
    if selected_type in LAYER_TYPES:
        st.caption(f"ℹ️ {LAYER_TYPES[selected_type]['description']}")


def render_layer_card(layer: dict, index: int, total_layers: int):
    """Render a single layer card with action buttons"""
    layer_id = layer["id"]
    layer_type = layer["type"]
    display_text = get_layer_display(layer)

    # Main container for the layer
    with st.container():
        col_num, col_info, col_actions = st.columns([0.5, 4, 2])

        with col_num:
            st.write(f"**{index + 1}.**")

        with col_info:
            st.write(display_text)

        with col_actions:
            btn_cols = st.columns(4)

            # Move up button
            with btn_cols[0]:
                if index > 0:
                    if st.button("↑", key=f"up_{layer_id}", help="Move layer earlier in the stack"):
                        move_layer_up(layer_id)
                        st.rerun()
                else:
                    st.write("")  # Disabled placeholder

            # Move down button
            with btn_cols[1]:
                if index < total_layers - 1:
                    if st.button("↓", key=f"down_{layer_id}", help="Move layer later in the stack"):
                        move_layer_down(layer_id)
                        st.rerun()
                else:
                    st.write("")  # Disabled placeholder

            # Edit button
            with btn_cols[2]:
                if LAYER_TYPES.get(layer_type, {}).get("params"):
                    if st.button("✏️", key=f"edit_{layer_id}", help="Edit layer parameters (filters, units, rates, etc.)"):
                        if is_editing(layer_id):
                            stop_editing()
                        else:
                            start_editing(layer_id)
                        st.rerun()
                else:
                    st.write("")  # No params to edit

            # Delete button
            with btn_cols[3]:
                if st.button("🗑️", key=f"del_{layer_id}", help="Remove this layer from the stack"):
                    remove_layer(layer_id)
                    st.rerun()

        # Edit panel (expanded when editing)
        if is_editing(layer_id):
            render_layer_editor(layer)


def render_layer_editor(layer: dict):
    """Render the parameter editor for a layer"""
    layer_id = layer["id"]
    layer_type = layer["type"]
    current_params = layer.get("params", {})
    layer_config = LAYER_TYPES.get(layer_type, {})
    param_configs = layer_config.get("params", {})

    with st.container():
        st.markdown("---")
        st.write(f"**Editing: {layer_config.get('display_name', layer_type)}**")

        new_params = {}

        # Create columns based on number of params
        num_params = len(param_configs)
        if num_params > 0:
            cols = st.columns(min(num_params, 3))

            for i, (param_name, config) in enumerate(param_configs.items()):
                with cols[i % len(cols)]:
                    current_value = current_params.get(param_name, config["default"])

                    if config["type"] == "select":
                        new_value = st.selectbox(
                            param_name.replace("_", " ").title(),
                            options=config["options"],
                            index=config["options"].index(current_value)
                            if current_value in config["options"]
                            else 0,
                            key=f"edit_{layer_id}_{param_name}",
                        )
                    elif config["type"] == "slider":
                        new_value = st.slider(
                            param_name.replace("_", " ").title(),
                            min_value=config["min"],
                            max_value=config["max"],
                            value=float(current_value),
                            step=config["step"],
                            key=f"edit_{layer_id}_{param_name}",
                        )
                    else:
                        new_value = current_value

                    new_params[param_name] = new_value

        # Save/Cancel buttons
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("Save", key=f"save_{layer_id}", type="primary"):
                update_layer(layer_id, new_params)
                stop_editing()
                st.rerun()

        with col2:
            if st.button("Cancel", key=f"cancel_{layer_id}"):
                stop_editing()
                st.rerun()

        with col3:
            if st.button("Duplicate Layer", key=f"dup_{layer_id}", help="Create a copy of this layer with the same parameters"):
                duplicate_layer(layer_id)
                stop_editing()
                st.rerun()

        st.markdown("---")


def render_layer_stack():
    """Render the complete layer stack"""
    layer_stack = get_layer_stack()

    if not layer_stack:
        st.info("📭 Layer stack is empty. Add layers or load a preset.")
        return

    st.subheader(f"Layer Stack ({len(layer_stack)} layers)")

    for i, layer in enumerate(layer_stack):
        render_layer_card(layer, i, len(layer_stack))


def render_output_layer(num_classes: int):
    """Render the fixed output layer"""
    st.markdown(
        f"**Output Layer:** 🎯 Dense | {num_classes} classes, softmax *(auto-configured)*"
    )


# def render_architecture_preview():
#     """Render a visual preview of the architecture"""
#     layer_stack = get_layer_stack()

#     if not layer_stack:
#         return

#     with st.expander("Architecture Preview", expanded=False):
#         # Build preview string
#         preview_parts = ["Input(224,224,3)"]

#         for layer in layer_stack:
#             layer_type = layer["type"]
#             params = layer.get("params", {})

#             if layer_type == "Conv2D":
#                 preview_parts.append(f"Conv2D({params.get('filters', '?')})")
#             elif layer_type == "MaxPooling2D":
#                 preview_parts.append("MaxPool")
#             elif layer_type == "AveragePooling2D":
#                 preview_parts.append("AvgPool")
#             elif layer_type == "BatchNorm":
#                 preview_parts.append("BN")
#             elif layer_type == "Dropout":
#                 preview_parts.append(f"Drop({params.get('rate', '?')})")
#             elif layer_type == "Flatten":
#                 preview_parts.append("Flatten")
#             elif layer_type == "GlobalAvgPool":
#                 preview_parts.append("GAP")
#             elif layer_type == "Dense":
#                 preview_parts.append(f"Dense({params.get('units', '?')})")

#         preview_parts.append("Output(softmax)")

#         st.code(" → ".join(preview_parts), language=None)


def render_validation_status():
    """Render validation status of the layer stack"""
    layer_stack = get_layer_stack()
    is_valid, errors = validate_layer_stack(layer_stack)

    if is_valid:
        st.success("✅ Architecture is valid")
    else:
        st.error("❌ Architecture has issues:")
        for error in errors:
            st.write(f"  • {error}")

    return is_valid
