"""Activation and filter visualization utilities."""

from typing import Any

import numpy as np
import torch
import torch.nn as nn


def get_activation_maps(
    model: nn.Module,
    device: torch.device,
    image_tensor: torch.Tensor,
    target_layer: nn.Module,
) -> np.ndarray:
    """
    Get activation maps for a specific layer.

    Args:
        model: The model
        device: Compute device
        image_tensor: (C, H, W) image tensor
        target_layer: Layer to visualize

    Returns:
        Activation maps as (num_filters, H, W) numpy array
    """
    activations = []

    def hook_fn(_module: Any, _inp: Any, output: torch.Tensor) -> None:
        activations.append(output.detach().cpu())

    handle = target_layer.register_forward_hook(hook_fn)

    try:
        model.eval()
        with torch.no_grad():
            input_tensor = image_tensor.unsqueeze(0).to(device)
            _ = model(input_tensor)

        if not activations:
            return np.array([])

        acts = activations[0].squeeze(0).numpy()
        return acts

    finally:
        handle.remove()


def get_filter_weights(layer: nn.Module) -> np.ndarray | None:
    """
    Get convolutional filter weights for visualization.

    Args:
        layer: Conv2d layer

    Returns:
        Filter weights as (out_channels, in_channels, kH, kW) numpy array
    """
    if not isinstance(layer, nn.Conv2d):
        return None

    weights = layer.weight.detach().cpu().numpy()
    return weights


def normalize_filter_for_display(filter_weights: np.ndarray) -> np.ndarray:
    """Normalize filter weights to [0, 1] for display."""
    min_val = filter_weights.min()
    max_val = filter_weights.max()
    if max_val - min_val > 0:
        return (filter_weights - min_val) / (max_val - min_val)
    return np.zeros_like(filter_weights)
