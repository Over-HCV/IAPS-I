"""Architecture analysis utilities."""

import time
from typing import Any

import numpy as np
import torch
import torch.nn as nn


def get_architecture_summary(model: nn.Module) -> dict[str, Any]:
    """
    Get detailed architecture summary.

    Returns:
        Dict with layers info, total params, trainable params, model size
    """
    layers_info = []
    total_params = 0
    trainable_params = 0

    for name, module in model.named_modules():
        if len(list(module.children())) > 0:
            continue

        params = sum(p.numel() for p in module.parameters())
        trainable = sum(p.numel() for p in module.parameters() if p.requires_grad)

        total_params += params
        trainable_params += trainable

        layer_type = module.__class__.__name__

        shape_str = ""
        if isinstance(module, nn.Linear):
            shape_str = f"({module.in_features} → {module.out_features})"
        elif isinstance(module, nn.Conv2d):
            shape_str = f"({module.in_channels} → {module.out_channels}, k={module.kernel_size})"
        elif isinstance(module, nn.BatchNorm2d):
            shape_str = f"({module.num_features})"

        layers_info.append({
            "name": name or "root",
            "type": layer_type,
            "shape": shape_str,
            "params": params,
            "trainable": trainable > 0,
        })

    model_size_mb = (total_params * 4) / (1024 * 1024)

    return {
        "layers": layers_info,
        "total_params": total_params,
        "trainable_params": trainable_params,
        "model_size_mb": model_size_mb,
    }


def measure_inference_time(
    model: nn.Module,
    device: torch.device,
    input_size: tuple = (1, 3, 224, 224),
    n_runs: int = 10,
) -> float:
    """Measure average inference time in milliseconds."""
    model.eval()
    dummy_input = torch.randn(*input_size).to(device)

    # Warmup
    with torch.no_grad():
        for _ in range(3):
            _ = model(dummy_input)

    if device.type == "cuda":
        torch.cuda.synchronize()

    times = []

    with torch.no_grad():
        for _ in range(n_runs):
            start = time.perf_counter()
            _ = model(dummy_input)
            if device.type == "cuda":
                torch.cuda.synchronize()
            times.append((time.perf_counter() - start) * 1000)

    return float(np.mean(times))
