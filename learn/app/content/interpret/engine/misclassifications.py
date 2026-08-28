"""Misclassification analysis utilities."""

import numpy as np
from PIL import Image
import torch
import torch.nn as nn


def get_misclassifications(
    model: nn.Module,
    device: torch.device,
    test_loader,
    class_names: list[str],
    n_samples: int = 50,
) -> list[dict]:
    """
    Find misclassified samples from test set.

    Returns:
        List of dicts with image info, true/predicted labels, confidence
    """
    model.eval()
    misclassified = []

    with torch.no_grad():
        for batch_idx, (inputs, targets) in enumerate(test_loader):
            inputs = inputs.to(device)
            outputs = model(inputs)
            probs = torch.softmax(outputs, dim=1)
            confidences, predicted = probs.max(1)

            mask = predicted.cpu() != targets
            indices = torch.where(mask)[0]

            for idx in indices:
                if len(misclassified) >= n_samples:
                    break

                i = idx.item()
                misclassified.append(
                    {
                        "batch_idx": batch_idx,
                        "sample_idx": i,
                        "true_label": targets[i].item(),
                        "true_class": class_names[targets[i].item()],
                        "pred_label": predicted[i].cpu().item(),
                        "pred_class": class_names[predicted[i].cpu().item()],
                        "confidence": confidences[i].cpu().item(),
                        "image_tensor": inputs[i].cpu(),
                    }
                )

            if len(misclassified) >= n_samples:
                break

    return misclassified


def tensor_to_image(tensor: torch.Tensor) -> Image.Image:
    """Convert a tensor (C, H, W) to PIL Image."""
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)

    tensor = tensor.cpu()

    if tensor.min() < 0:
        tensor = tensor * std + mean

    tensor = tensor.clamp(0, 1)
    img_array = (tensor.permute(1, 2, 0).numpy() * 255).astype(np.uint8)

    return Image.fromarray(img_array)
