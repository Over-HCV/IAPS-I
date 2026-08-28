"""
Tooltips for model configuration page.
Centralized tooltip text for architecture types, layers, and hyperparameters.
"""

# Model type descriptions
MODEL_TYPES = {
    "custom_cnn": {
        "name": "Custom CNN",
        "description": (
            "Build a Convolutional Neural Network from scratch. "
            "Full control over layer depth, filter counts, and regularization. "
            "Good for learning and experimentation."
        ),
    },
    "transformer": {
        "name": "Transformer (ViT)",
        "description": (
            "Vision Transformer architecture. State-of-the-art but requires "
            "large datasets and significant compute. Experimental for malware classification."
        ),
    },
    "transfer_learning": {
        "name": "Transfer Learning",
        "description": (
            "Use pre-trained models (ResNet, EfficientNet, VGG) fine-tuned on your data. "
            "Recommended approach: faster training, better results with limited data."
        ),
    },
}

# CNN layer tooltips
CNN_TOOLTIPS = {
    "conv_filters": (
        "Number of filters (kernels) in each convolutional layer. "
        "More filters capture more features but increase computation. "
        "Common pattern: double filters as spatial size halves (32→64→128)."
    ),
    "kernel_size": (
        "Size of the convolutional kernel (e.g., 3x3). "
        "Smaller kernels (3x3) are computationally efficient and stack well. "
        "Larger kernels (5x5, 7x7) capture broader patterns but cost more."
    ),
    "stride": (
        "Step size when sliding the kernel across the image. "
        "Stride 1: preserves spatial dimensions. "
        "Stride 2: halves spatial dimensions (downsampling)."
    ),
    "padding": (
        "Pixels added around the image border. "
        "'same' preserves dimensions, 'valid' reduces dimensions."
    ),
    "pooling": (
        "Downsamples feature maps to reduce computation and add translation invariance. "
        "MaxPool keeps strongest activations. AvgPool keeps average response."
    ),
    "batch_norm": (
        "Normalizes layer outputs to stabilize training. "
        "Allows higher learning rates and reduces sensitivity to initialization. "
        "Generally recommended for deeper networks."
    ),
    "dropout": (
        "Randomly zeroes neurons during training to prevent overfitting. "
        "Typical values: 0.2-0.5. Higher values = stronger regularization."
    ),
    "dense_units": (
        "Number of neurons in fully-connected layers after convolutions. "
        "Learns to combine spatial features for classification."
    ),
    "activation": (
        "Non-linear function applied after each layer. "
        "ReLU: fast, works well in most cases. "
        "LeakyReLU: prevents 'dying ReLU' problem."
    ),
}

# Transfer learning tooltips
TRANSFER_TOOLTIPS = {
    "base_model": (
        "Pre-trained architecture to use as feature extractor. "
        "ResNet: residual connections, good all-rounder. "
        "EfficientNet: optimized for efficiency. "
        "VGG: simpler but larger."
    ),
    "weights": (
        "Pre-trained weights to initialize the model. "
        "ImageNet: trained on 1M+ natural images. "
        "Provides good general visual features."
    ),
    "strategy": (
        "How to use the pre-trained model. "
        "Feature Extraction: freeze base, train only classifier. Fast, good baseline. "
        "Fine-tuning: unfreeze some layers, train end-to-end. Better but slower."
    ),
    "unfreeze_layers": (
        "Number of layers to unfreeze from the top of the base model. "
        "More layers = more parameters to train = needs more data. "
        "Start with few layers, increase if underfitting."
    ),
    "global_pooling": (
        "Reduces spatial dimensions to a single vector per feature map. "
        "Global Average Pooling: averages all spatial positions. "
        "Reduces overfitting compared to flattening."
    ),
}

# Transformer (ViT) tooltips
TRANSFORMER_TOOLTIPS = {
    "patch_size": (
        "Size of image patches (e.g., 16x16 pixels). "
        "Smaller patches = more tokens = higher cost but finer detail. "
        "Common values: 16 or 32."
    ),
    "embed_dim": (
        "Embedding dimension for each patch token. "
        "Larger = more capacity but more parameters. "
        "Common values: 192 (tiny), 384 (small), 768 (base)."
    ),
    "depth": (
        "Number of transformer encoder blocks. "
        "Deeper = more capacity but harder to train. "
        "Common values: 6 (tiny), 12 (base), 24 (large)."
    ),
    "num_heads": (
        "Number of attention heads in multi-head attention. "
        "Must divide embed_dim evenly. More heads = different attention patterns."
    ),
    "mlp_ratio": (
        "Expansion ratio for the feedforward network. "
        "MLP hidden dim = embed_dim × mlp_ratio. "
        "Common value: 4.0."
    ),
}

# Architecture summary tooltips
SUMMARY_TOOLTIPS = {
    "total_params": (
        "Total number of learnable parameters in the model. "
        "More parameters = more capacity but needs more data and compute."
    ),
    "trainable_params": (
        "Parameters that will be updated during training. "
        "In transfer learning, some parameters may be frozen."
    ),
    "model_size": (
        "Approximate memory size of the model in MB. "
        "Affects GPU memory usage during training."
    ),
    "flops": (
        "Floating-point operations per forward pass. "
        "Indicates computational cost per image."
    ),
}
