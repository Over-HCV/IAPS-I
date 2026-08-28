"""Vision Transformer configuration UI"""

import streamlit as st


def _init_state():
    """Initialize transformer session state defaults"""
    if "transformer_patch_size" not in st.session_state:
        st.session_state.transformer_patch_size = 16
    if "transformer_embed_dim" not in st.session_state:
        st.session_state.transformer_embed_dim = 768
    if "transformer_depth" not in st.session_state:
        st.session_state.transformer_depth = 12
    if "transformer_num_heads" not in st.session_state:
        st.session_state.transformer_num_heads = 12
    if "transformer_mlp_ratio" not in st.session_state:
        st.session_state.transformer_mlp_ratio = 4.0
    if "transformer_dropout" not in st.session_state:
        st.session_state.transformer_dropout = 0.1


def render(num_classes: int) -> dict:
    """Configure Vision Transformer model"""
    _init_state()

    st.header("Vision Transformer Configuration")

    st.info("Custom Vision Transformer (ViT) implementation")

    # Patch and Embedding Configuration
    st.subheader("Patch & Embedding Configuration")

    col1, col2 = st.columns(2)

    with col1:
        patch_size = st.selectbox(
            "Patch Size",
            options=[8, 14, 16, 32],
            key="transformer_patch_size",
            help="Image is split into NxN patches. Smaller = more patches = more detail but higher compute. 16 is standard for 224x224 images.",
        )

        embed_dim = st.selectbox(
            "Embedding Dimension",
            options=[384, 512, 768, 1024],
            key="transformer_embed_dim",
            help="Size of patch embeddings. Larger = more capacity but more parameters. 768 is ViT-Base, 1024 is ViT-Large.",
        )

    with col2:
        depth = st.slider(
            "Transformer Depth",
            min_value=6,
            max_value=24,
            key="transformer_depth",
            help="Number of stacked transformer blocks. More depth = more abstraction but slower training. ViT-Base uses 12.",
        )

        num_heads = st.selectbox(
            "Attention Heads",
            options=[6, 8, 12, 16],
            key="transformer_num_heads",
            help="Parallel attention mechanisms per block. Must divide embed_dim evenly. More heads = finer-grained attention patterns.",
        )

    # MLP Configuration
    st.subheader("MLP Configuration")

    col1, col2 = st.columns(2)

    with col1:
        mlp_ratio = st.slider(
            "MLP Ratio",
            min_value=2.0,
            max_value=8.0,
            step=0.5,
            key="transformer_mlp_ratio",
            help="Feed-forward network size = embed_dim × ratio. Higher ratio = more capacity per block. Standard is 4.0.",
        )

    with col2:
        dropout = st.slider(
            "Dropout Rate",
            min_value=0.0,
            max_value=0.5,
            key="transformer_dropout",
            help="Applied in attention and MLP layers. Helps prevent overfitting. 0.1 is typical for ViT.",
        )

    # Display estimated parameters
    num_patches = (224 // patch_size) ** 2
    st.info(
        f"Image will be split into {num_patches} patches of size {patch_size}x{patch_size}"
    )
    st.info(f"Output Layer: {num_classes} units with Softmax activation")

    return {
        "patch_size": patch_size,
        "embed_dim": embed_dim,
        "depth": depth,
        "num_heads": num_heads,
        "mlp_ratio": mlp_ratio,
        "dropout": dropout,
        "num_classes": num_classes,
        "num_patches": num_patches,
    }
