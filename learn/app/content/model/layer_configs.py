"""
Layer Configuration - Defines layer types and presets for CNN builder
"""

from typing import Any

# Available layer types with their parameters and defaults
LAYER_TYPES = {
    "Conv2D": {
        "display_name": "Convolutional 2D",
        "icon": "🔲",
        "category": "feature_extraction",
        "params": {
            "filters": {
                "type": "select",
                "options": [16, 32, 64, 128, 256, 512],
                "default": 32,
            },
            "kernel_size": {"type": "select", "options": [1, 3, 5, 7], "default": 3},
            "activation": {
                "type": "select",
                "options": ["relu", "leaky_relu", "gelu", "swish", "none"],
                "default": "relu",
            },
            "padding": {
                "type": "select",
                "options": ["same", "valid"],
                "default": "same",
            },
        },
        "description": "Extracts features using learnable filters",
    },
    "MaxPooling2D": {
        "display_name": "Max Pooling 2D",
        "icon": "⬇️",
        "category": "feature_extraction",
        "params": {
            "pool_size": {"type": "select", "options": [2, 3, 4], "default": 2},
        },
        "description": "Reduces spatial dimensions by taking max value",
    },
    "AveragePooling2D": {
        "display_name": "Average Pooling 2D",
        "icon": "📊",
        "category": "feature_extraction",
        "params": {
            "pool_size": {"type": "select", "options": [2, 3, 4], "default": 2},
        },
        "description": "Reduces spatial dimensions by taking average",
    },
    "BatchNorm": {
        "display_name": "Batch Normalization",
        "icon": "📏",
        "category": "normalization",
        "params": {},
        "description": "Normalizes activations for faster training",
    },
    "Dropout": {
        "display_name": "Dropout",
        "icon": "💧",
        "category": "regularization",
        "params": {
            "rate": {
                "type": "slider",
                "min": 0.0,
                "max": 0.7,
                "step": 0.05,
                "default": 0.25,
            },
        },
        "description": "Randomly drops neurons for regularization",
    },
    "Flatten": {
        "display_name": "Flatten",
        "icon": "📐",
        "category": "transition",
        "params": {},
        "description": "Converts 2D feature maps to 1D vector",
    },
    "GlobalAvgPool": {
        "display_name": "Global Average Pooling",
        "icon": "🌐",
        "category": "transition",
        "params": {},
        "description": "Alternative to Flatten - averages each feature map",
    },
    "Dense": {
        "display_name": "Dense (Fully Connected)",
        "icon": "🧠",
        "category": "classification",
        "params": {
            "units": {
                "type": "select",
                "options": [64, 128, 256, 512, 1024],
                "default": 256,
            },
            "activation": {
                "type": "select",
                "options": ["relu", "leaky_relu", "gelu", "swish", "none"],
                "default": "relu",
            },
        },
        "description": "Fully connected layer for classification",
    },
}

# Preset architectures
PRESETS = {
    "profesor": {
        "name": "Conventional",
        "description": "Conv → Conv → Pool → Conv → Conv → Pool → Dropout → Flatten → Dense → Dropout → Dense → Dropout",
        "layers": [
            {
                "type": "Conv2D",
                "params": {
                    "filters": 32,
                    "kernel_size": 3,
                    "activation": "relu",
                    "padding": "same",
                },
            },
            {
                "type": "Conv2D",
                "params": {
                    "filters": 32,
                    "kernel_size": 3,
                    "activation": "relu",
                    "padding": "same",
                },
            },
            {"type": "MaxPooling2D", "params": {"pool_size": 2}},
            {
                "type": "Conv2D",
                "params": {
                    "filters": 64,
                    "kernel_size": 3,
                    "activation": "relu",
                    "padding": "same",
                },
            },
            {
                "type": "Conv2D",
                "params": {
                    "filters": 64,
                    "kernel_size": 3,
                    "activation": "relu",
                    "padding": "same",
                },
            },
            {"type": "MaxPooling2D", "params": {"pool_size": 2}},
            {"type": "Dropout", "params": {"rate": 0.25}},
            {"type": "Flatten", "params": {}},
            {"type": "Dense", "params": {"units": 512, "activation": "relu"}},
            {"type": "Dropout", "params": {"rate": 0.5}},
            {"type": "Dense", "params": {"units": 256, "activation": "relu"}},
            {"type": "Dropout", "params": {"rate": 0.5}},
        ],
    },
    "lenet": {
        "name": "LeNet-style (Simple)",
        "description": "Classic architecture: 2 Conv+Pool blocks, then Dense layers",
        "layers": [
            {
                "type": "Conv2D",
                "params": {
                    "filters": 32,
                    "kernel_size": 5,
                    "activation": "relu",
                    "padding": "same",
                },
            },
            {"type": "MaxPooling2D", "params": {"pool_size": 2}},
            {
                "type": "Conv2D",
                "params": {
                    "filters": 64,
                    "kernel_size": 5,
                    "activation": "relu",
                    "padding": "same",
                },
            },
            {"type": "MaxPooling2D", "params": {"pool_size": 2}},
            {"type": "Flatten", "params": {}},
            {"type": "Dense", "params": {"units": 256, "activation": "relu"}},
            {"type": "Dropout", "params": {"rate": 0.5}},
        ],
    },
    "vgg_mini": {
        "name": "VGG-style (Deep)",
        "description": "Deeper architecture with blocks of Conv-Conv-Pool",
        "layers": [
            {
                "type": "Conv2D",
                "params": {
                    "filters": 64,
                    "kernel_size": 3,
                    "activation": "relu",
                    "padding": "same",
                },
            },
            {
                "type": "Conv2D",
                "params": {
                    "filters": 64,
                    "kernel_size": 3,
                    "activation": "relu",
                    "padding": "same",
                },
            },
            {"type": "MaxPooling2D", "params": {"pool_size": 2}},
            {
                "type": "Conv2D",
                "params": {
                    "filters": 128,
                    "kernel_size": 3,
                    "activation": "relu",
                    "padding": "same",
                },
            },
            {
                "type": "Conv2D",
                "params": {
                    "filters": 128,
                    "kernel_size": 3,
                    "activation": "relu",
                    "padding": "same",
                },
            },
            {"type": "MaxPooling2D", "params": {"pool_size": 2}},
            {
                "type": "Conv2D",
                "params": {
                    "filters": 256,
                    "kernel_size": 3,
                    "activation": "relu",
                    "padding": "same",
                },
            },
            {
                "type": "Conv2D",
                "params": {
                    "filters": 256,
                    "kernel_size": 3,
                    "activation": "relu",
                    "padding": "same",
                },
            },
            {"type": "MaxPooling2D", "params": {"pool_size": 2}},
            {"type": "Flatten", "params": {}},
            {"type": "Dense", "params": {"units": 512, "activation": "relu"}},
            {"type": "Dropout", "params": {"rate": 0.5}},
            {"type": "Dense", "params": {"units": 256, "activation": "relu"}},
            {"type": "Dropout", "params": {"rate": 0.5}},
        ],
    },
    "empty": {
        "name": "Empty (Start from scratch)",
        "description": "Start with an empty layer stack",
        "layers": [],
    },
}


def get_default_params(layer_type: str) -> dict[str, Any]:
    """Get default parameters for a layer type"""
    if layer_type not in LAYER_TYPES:
        return {}

    params = {}
    for param_name, param_config in LAYER_TYPES[layer_type]["params"].items():
        params[param_name] = param_config["default"]

    return params


def get_layer_display(layer: dict) -> str:
    """Get a display string for a layer"""
    layer_type = layer["type"]
    params = layer.get("params", {})

    config = LAYER_TYPES.get(layer_type, {})
    icon = config.get("icon", "❓")

    if layer_type == "Conv2D":
        return f"{icon} Conv2D | {params.get('filters', '?')} filters, {params.get('kernel_size', '?')}x{params.get('kernel_size', '?')}, {params.get('activation', '?')}"
    elif layer_type in ["MaxPooling2D", "AveragePooling2D"]:
        return f"{icon} {layer_type} | {params.get('pool_size', '?')}x{params.get('pool_size', '?')}"
    elif layer_type == "Dropout":
        return f"{icon} Dropout | rate={params.get('rate', '?')}"
    elif layer_type == "Dense":
        return f"{icon} Dense | {params.get('units', '?')} units, {params.get('activation', '?')}"
    elif layer_type in ["Flatten", "GlobalAvgPool", "BatchNorm"]:
        return f"{icon} {layer_type}"
    else:
        return f"{icon} {layer_type}"


def validate_layer_stack(layer_stack: list[dict]) -> tuple[bool, list[str]]:
    """
    Validate a layer stack for common errors.
    Returns (is_valid, list_of_errors)
    """
    errors = []

    if not layer_stack:
        errors.append("Layer stack is empty. Add at least one layer.")
        return False, errors

    # Check for at least one Conv layer
    has_conv = any(l["type"] == "Conv2D" for l in layer_stack)
    if not has_conv:
        errors.append("Add at least one Conv2D layer for feature extraction.")

    # Find transition point (Flatten or GlobalAvgPool)
    transition_idx = -1
    for i, layer in enumerate(layer_stack):
        if layer["type"] in ["Flatten", "GlobalAvgPool"]:
            transition_idx = i
            break

    # Check for Dense without transition
    for i, layer in enumerate(layer_stack):
        if layer["type"] == "Dense" and transition_idx == -1:
            errors.append("Add Flatten or GlobalAvgPool before Dense layers.")
            break
        if layer["type"] == "Dense" and i < transition_idx:
            errors.append(
                f"Dense layer at position {i + 1} appears before Flatten/GlobalAvgPool."
            )

    # Check for Conv after transition
    if transition_idx >= 0:
        for i, layer in enumerate(
            layer_stack[transition_idx + 1 :], start=transition_idx + 1
        ):
            if layer["type"] == "Conv2D":
                errors.append(
                    f"Conv2D at position {i + 1} appears after Flatten/GlobalAvgPool."
                )

    # Check for at least one Dense layer (for classification)
    has_dense = any(l["type"] == "Dense" for l in layer_stack)
    if not has_dense:
        errors.append("Add at least one Dense layer for classification.")

    return len(errors) == 0, errors
