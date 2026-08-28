"""
Training Configuration Page
Form-based training config with sidebar library
"""

from content.training.tooltips import (
    EARLY_STOPPING_TOOLTIPS,
    HYPERPARAMETER_TOOLTIPS,
    OPTIMIZER_TOOLTIPS,
    SCHEDULER_TOOLTIPS,
)
from state.workflow import (
    add_training_to_library,
    delete_training_from_library,
    get_training_from_library,
    get_training_library,
    update_training_in_library,
)
import streamlit as st


def render():
    """Main render function for Training page"""
    st.title(
        "Training Configuration", help="Configure hyperparameters for model training."
    )

    # Initialize state
    if "training_selected_id" not in st.session_state:
        st.session_state.training_selected_id = None
    if "training_config_name" not in st.session_state:
        st.session_state.training_config_name = ""

    # Layout: sidebar list + main form
    # Sidebar renders FIRST to process actions before widgets are instantiated
    col_sidebar, col_main = st.columns([1, 3])

    with col_sidebar:
        _render_config_sidebar()

    with col_main:
        config = _render_training_form()
        _render_save_section(config)


def _render_config_sidebar():
    """Render the sidebar with saved configs"""
    st.subheader("Saved Configs")

    configs = get_training_library()

    if not configs:
        st.caption("No saved configs yet")
    else:
        for cfg in configs:
            col1, col2 = st.columns([4, 1])
            with col1:
                is_selected = st.session_state.training_selected_id == cfg["id"]
                if st.button(
                    f"{'●' if is_selected else '○'} {cfg['name']}",
                    key=f"sel_{cfg['id']}",
                    width="stretch",
                ):
                    _load_config(cfg["id"])
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{cfg['id']}", help="Delete"):
                    delete_training_from_library(cfg["id"])
                    if st.session_state.training_selected_id == cfg["id"]:
                        st.session_state.training_selected_id = None
                    st.rerun()

    st.divider()

    if st.button("+ New Config", width="stretch"):
        st.session_state.training_selected_id = None
        st.session_state.training_config_name = ""
        _reset_form_to_defaults()
        st.rerun()


def _load_config(config_id: str):
    """Load a config into the form"""
    cfg = get_training_from_library(config_id)
    if not cfg:
        return

    st.session_state.training_selected_id = config_id
    st.session_state.training_config_name = cfg["name"]

    config = cfg.get("config", {})

    # Load all values into session state
    st.session_state.train_optimizer = config.get("optimizer", "Adam")
    st.session_state.train_lr = config.get("learning_rate", 0.001)
    st.session_state.train_lr_strategy = config.get("lr_strategy", "Constant")
    st.session_state.train_epochs = config.get("epochs", 100)
    st.session_state.train_batch_size = config.get("batch_size", 32)
    st.session_state.train_shuffle = config.get("shuffle", True)
    st.session_state.train_l2 = config.get("l2_decay", False)
    st.session_state.train_l2_lambda = config.get("l2_lambda", 0.0001)
    st.session_state.train_class_weights = config.get(
        "class_weights", "Auto Class Weights"
    )
    st.session_state.train_early_stopping = config.get("early_stopping", True)
    st.session_state.train_es_patience = config.get("es_patience", 10)
    st.session_state.train_checkpointing = config.get("checkpointing", True)
    st.session_state.train_checkpoint_metric = config.get(
        "checkpoint_metric", "Val Loss"
    )


def _reset_form_to_defaults():
    """Reset form to default values"""
    st.session_state.train_optimizer = "Adam"
    st.session_state.train_lr = 0.001
    st.session_state.train_lr_strategy = "Constant"
    st.session_state.train_epochs = 100
    st.session_state.train_batch_size = 32
    st.session_state.train_shuffle = True
    st.session_state.train_l2 = False
    st.session_state.train_l2_lambda = 0.0001
    st.session_state.train_class_weights = "Auto Class Weights"
    st.session_state.train_early_stopping = True
    st.session_state.train_es_patience = 10
    st.session_state.train_checkpointing = True
    st.session_state.train_checkpoint_metric = "Val Loss"


def _render_training_form() -> dict:
    """Render the training configuration form"""
    # Config name
    name = st.text_input(
        "Config Name",
        value=st.session_state.get("training_config_name", ""),
        placeholder="e.g., Adam_Default",
        help="Name for this training configuration",
    )
    st.session_state.training_config_name = name

    st.divider()

    # Optimizer
    st.subheader(
        "Optimizer", help="Algorithm that updates model weights during training."
    )
    col1, col2 = st.columns(2)

    with col1:
        optimizer = st.selectbox(
            "Optimizer",
            ["Adam", "AdamW", "SGD with Momentum", "RMSprop"],
            key="train_optimizer",
            help=OPTIMIZER_TOOLTIPS.get(
                st.session_state.get("train_optimizer", "Adam")
                .lower()
                .replace(" with momentum", ""),
                "",
            ),
        )

    with col2:
        lr = st.slider(
            "Learning Rate",
            0.0001,
            0.01,
            step=0.0001,
            key="train_lr",
            format="%.4f",
            help=HYPERPARAMETER_TOOLTIPS["learning_rate"],
        )

    # LR Scheduler
    st.subheader(
        "Learning Rate Schedule",
        help="Adjust learning rate during training to improve convergence.",
    )
    lr_strategy = st.radio(
        "Strategy",
        ["Constant", "ReduceLROnPlateau", "Cosine Annealing"],
        key="train_lr_strategy",
        horizontal=True,
        help=SCHEDULER_TOOLTIPS.get(
            st.session_state.get("train_lr_strategy", "Constant")
            .lower()
            .replace(" ", "_"),
            "How learning rate changes during training.",
        ),
    )

    # Training parameters
    st.subheader("Training Parameters", help="Core training loop settings.")
    col1, col2, col3 = st.columns(3)

    with col1:
        epochs = st.slider(
            "Max Epochs",
            10,
            200,
            key="train_epochs",
            help=HYPERPARAMETER_TOOLTIPS["epochs"],
        )

    with col2:
        batch_size = st.selectbox(
            "Batch Size",
            [16, 32, 64, 128],
            key="train_batch_size",
            help=HYPERPARAMETER_TOOLTIPS["batch_size"],
        )

    with col3:
        shuffle = st.checkbox("Shuffle Data", key="train_shuffle")

    # Regularization
    st.subheader(
        "Regularization",
        help="Techniques to prevent overfitting by constraining model complexity.",
    )
    col1, col2 = st.columns(2)

    with col1:
        l2 = st.checkbox(
            "L2 Weight Decay",
            key="train_l2",
            help=HYPERPARAMETER_TOOLTIPS["weight_decay"],
        )

    with col2:
        if l2:
            l2_lambda = st.slider(
                "Lambda",
                0.0001,
                0.01,
                step=0.0001,
                key="train_l2_lambda",
                format="%.4f",
            )
        else:
            l2_lambda = 0.0001

    # Class imbalance
    st.subheader("Class Imbalance")
    class_weights = st.radio(
        "Method",
        ["Auto Class Weights", "Focal Loss", "None"],
        key="train_class_weights",
        horizontal=True,
        help="Handle imbalanced classes.",
    )

    # Callbacks
    st.subheader(
        "Callbacks",
        help="Automated actions during training: early stopping and checkpointing.",
    )
    col1, col2 = st.columns(2)

    with col1:
        early_stopping = st.checkbox(
            "Early Stopping",
            key="train_early_stopping",
            help=EARLY_STOPPING_TOOLTIPS["enabled"],
        )
        if early_stopping:
            es_patience = st.slider(
                "Patience",
                5,
                30,
                key="train_es_patience",
                help=EARLY_STOPPING_TOOLTIPS["patience"],
            )
        else:
            es_patience = 10

    with col2:
        checkpointing = st.checkbox("Model Checkpointing", key="train_checkpointing")
        if checkpointing:
            checkpoint_metric = st.radio(
                "Save Best By",
                ["Val Loss", "Val Accuracy"],
                key="train_checkpoint_metric",
            )
        else:
            checkpoint_metric = "Val Loss"

    # Build config dict
    return {
        "optimizer": optimizer,
        "learning_rate": lr,
        "lr_strategy": lr_strategy,
        "epochs": epochs,
        "batch_size": batch_size,
        "shuffle": shuffle,
        "l2_decay": l2,
        "l2_lambda": l2_lambda if l2 else 0,
        "class_weights": class_weights,
        "early_stopping": early_stopping,
        "es_patience": es_patience if early_stopping else 0,
        "checkpointing": checkpointing,
        "checkpoint_metric": checkpoint_metric if checkpointing else None,
    }


def _render_save_section(config: dict):
    """Render save/update buttons"""
    st.divider()

    name = st.session_state.get("training_config_name", "").strip()
    is_editing = st.session_state.training_selected_id is not None

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if not name:
            st.warning("Enter a config name to save")

    with col2:
        if st.button(
            "Save as New",
            width="stretch",
            disabled=not name,
            type="primary" if not is_editing else "secondary",
        ):
            add_training_to_library(name, config)
            st.success(f"Config '{name}' saved!")
            st.session_state.training_config_name = ""
            st.session_state.training_selected_id = None
            st.rerun()

    with col3:
        if is_editing:
            if st.button("Update", width="stretch", disabled=not name):
                update_training_in_library(
                    st.session_state.training_selected_id, name, config
                )
                st.success(f"Config '{name}' updated!")
                st.rerun()
