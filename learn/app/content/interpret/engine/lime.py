"""LIME explanation utilities."""

from content.interpret.engine.misclassifications import tensor_to_image
import numpy as np
import torch
import torch.nn as nn


def compute_lime_explanation(
    model: nn.Module,
    device: torch.device,
    image_tensor: torch.Tensor,
    class_names: list[str],
    num_samples: int = 100,
    num_features: int = 10,
) -> dict:
    """
    Compute a simple LIME-like explanation using superpixel perturbation.

    Args:
        model: The model
        device: Compute device
        image_tensor: (C, H, W) image tensor
        class_names: List of class names
        num_samples: Number of perturbation samples
        num_features: Number of top features to return

    Returns:
        Dict with explanation data
    """
    from skimage.segmentation import quickshift
    from torchvision import transforms

    model.eval()

    img_np = tensor_to_image(image_tensor)
    img_array = np.array(img_np)

    segments = quickshift(img_array, kernel_size=4, max_dist=200, ratio=0.2)
    num_segments = segments.max() + 1

    with torch.no_grad():
        input_tensor = image_tensor.unsqueeze(0).to(device)
        output = model(input_tensor)
        probs = torch.softmax(output, dim=1)
        pred_class = output.argmax(dim=1).item()
        pred_prob = probs[0, pred_class].item()

    perturbation_masks = []
    predictions = []

    transform = transforms.ToTensor()

    for _ in range(num_samples):
        mask = np.random.randint(0, 2, num_segments).astype(bool)
        perturbation_masks.append(mask)

        perturbed = img_array.copy()
        for seg_idx in range(num_segments):
            if not mask[seg_idx]:
                perturbed[segments == seg_idx] = 128

        perturbed_tensor = transform(perturbed).to(device)

        with torch.no_grad():
            out = model(perturbed_tensor.unsqueeze(0))
            prob = torch.softmax(out, dim=1)[0, pred_class].item()
            predictions.append(prob)

    perturbation_masks = np.array(perturbation_masks)
    predictions = np.array(predictions)

    segment_importance = []
    for seg_idx in range(num_segments):
        present = perturbation_masks[:, seg_idx]
        if present.sum() > 0 and (~present).sum() > 0:
            importance = predictions[present].mean() - predictions[~present].mean()
        else:
            importance = 0
        segment_importance.append(importance)

    segment_importance = np.array(segment_importance)

    top_indices = np.argsort(np.abs(segment_importance))[-num_features:][::-1]

    explanation_mask = np.zeros_like(segments, dtype=float)
    for idx in top_indices:
        explanation_mask[segments == idx] = segment_importance[idx]

    if explanation_mask.max() > 0:
        pos_mask = np.maximum(explanation_mask, 0)
        pos_mask = pos_mask / (pos_mask.max() + 1e-8)
    else:
        pos_mask = np.zeros_like(explanation_mask)

    if explanation_mask.min() < 0:
        neg_mask = np.minimum(explanation_mask, 0)
        neg_mask = neg_mask / (abs(neg_mask.min()) + 1e-8)
    else:
        neg_mask = np.zeros_like(explanation_mask)

    return {
        "segments": segments,
        "num_segments": num_segments,
        "segment_importance": segment_importance,
        "top_segments": top_indices.tolist(),
        "explanation_mask": explanation_mask,
        "positive_mask": pos_mask,
        "negative_mask": neg_mask,
        "pred_class": pred_class,
        "pred_class_name": class_names[pred_class],
        "pred_prob": pred_prob,
    }
