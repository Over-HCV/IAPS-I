"""Grad-CAM visualization utilities."""

from typing import Any

import numpy as np
import torch
import torch.nn as nn


def get_conv_layers(model: nn.Module) -> list[tuple[str, nn.Module]]:
    """Get all Conv2d layers from the model."""
    conv_layers = []

    for name, module in model.named_modules():
        if isinstance(module, nn.Conv2d):
            conv_layers.append((name, module))

    return conv_layers


def compute_gradcam(
    model: nn.Module,
    device: torch.device,
    image_tensor: torch.Tensor,
    target_layer: nn.Module,
    target_class: int | None = None,
) -> tuple[np.ndarray, int, float]:
    """
    Compute Grad-CAM heatmap for an image.

    Args:
        model: The model
        device: Compute device
        image_tensor: (C, H, W) image tensor
        target_layer: Conv layer to visualize
        target_class: Class to explain (None = predicted class)

    Returns:
        Tuple of (heatmap, predicted_class, confidence)
    """
    gradients = []
    activations = []

    def forward_hook(_module: Any, _inp: Any, output: torch.Tensor) -> torch.Tensor:
        cloned = output.clone()
        activations.append(cloned)
        return cloned

    def backward_hook(_module: Any, _grad_input: Any, grad_output: tuple) -> None:
        gradients.append(grad_output[0].clone())

    forward_handle = target_layer.register_forward_hook(forward_hook)
    backward_handle = target_layer.register_full_backward_hook(backward_hook)

    # Track modules with inplace operations
    original_inplace = {}

    try:
        # Disable inplace operations to avoid autograd conflicts
        for name, module in model.named_modules():
            if hasattr(module, "inplace") and module.inplace:
                original_inplace[name] = True
                module.inplace = False

        input_tensor = image_tensor.unsqueeze(0).to(device).clone()
        input_tensor.requires_grad_(True)

        model.eval()

        output = model(input_tensor)
        probs = torch.softmax(output, dim=1)

        if target_class is None:
            target_class = output.argmax(dim=1).item()

        confidence = probs[0, target_class].item()

        model.zero_grad()
        if input_tensor.grad is not None:
            input_tensor.grad.zero_()

        one_hot = torch.zeros_like(output)
        one_hot[0, target_class] = 1

        output.backward(gradient=one_hot, retain_graph=True)

        if not gradients:
            raise RuntimeError("No gradients captured. Try a different layer.")

        grads = gradients[0]
        acts = activations[0]

        weights = grads.mean(dim=(2, 3), keepdim=True)
        cam = (weights * acts).sum(dim=1, keepdim=True)
        cam = torch.relu(cam)

        cam = cam - cam.min()
        if cam.max() > 0:
            cam = cam / cam.max()

        cam = torch.nn.functional.interpolate(
            cam, size=(224, 224), mode="bilinear", align_corners=False
        )

        heatmap = cam.squeeze().cpu().detach().numpy()

    finally:
        forward_handle.remove()
        backward_handle.remove()

        # Restore inplace operations
        for name, module in model.named_modules():
            if name in original_inplace:
                module.inplace = True

    return heatmap, target_class, confidence


def get_top_predictions(
    model: nn.Module,
    device: torch.device,
    image_tensor: torch.Tensor,
    class_names: list[str],
    top_k: int = 5,
) -> list[dict]:
    """Get top-k predictions for an image."""
    model.eval()

    with torch.no_grad():
        input_tensor = image_tensor.unsqueeze(0).to(device)
        output = model(input_tensor)
        probs = torch.softmax(output, dim=1)

        top_probs, top_indices = probs.topk(min(top_k, len(class_names)))

    predictions = []
    for prob, idx in zip(top_probs[0], top_indices[0], strict=True):
        predictions.append({
            "class_idx": idx.item(),
            "class_name": class_names[idx.item()],
            "confidence": prob.item(),
        })

    return predictions
