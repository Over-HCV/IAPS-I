"""Feature extraction and embedding utilities."""

from typing import Any

import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import davies_bouldin_score, silhouette_score
import torch
import torch.nn as nn


def extract_features(
    model: nn.Module,
    device: torch.device,
    dataloader,
    max_samples: int = 1000,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extract feature embeddings from model (before classifier).

    Returns:
        Tuple of (features, labels, predictions)
    """
    model.eval()

    features_list = []
    labels_list = []
    preds_list = []

    features_captured = []

    def hook_fn(_module: Any, _input: Any, output: torch.Tensor) -> None:
        if isinstance(output, torch.Tensor):
            features_captured.append(output.detach().cpu())

    hook_handle = None

    # For CustomCNN
    if hasattr(model, "feature_layers") and hasattr(model, "classifier_layers"):
        if not model.use_global_pool and len(model.feature_layers) > 0:
            hook_handle = model.feature_layers[-1].register_forward_hook(hook_fn)

    # For TransferModel
    elif hasattr(model, "base_model") and hasattr(model, "classifier"):
        hook_handle = model.base_model.register_forward_hook(hook_fn)

    samples_collected = 0

    with torch.no_grad():
        for inputs, targets in dataloader:
            if samples_collected >= max_samples:
                break

            inputs = inputs.to(device)
            features_captured.clear()

            outputs = model(inputs)
            _, predicted = outputs.max(1)

            if features_captured:
                batch_features = features_captured[0]
                if len(batch_features.shape) > 2:
                    batch_features = batch_features.view(batch_features.size(0), -1)
            else:
                batch_features = outputs.cpu()

            remaining = max_samples - samples_collected
            batch_features = batch_features[:remaining]
            targets = targets[:remaining]
            predicted = predicted.cpu()[:remaining]

            features_list.append(batch_features.numpy())
            labels_list.append(targets.numpy())
            preds_list.append(predicted.numpy())

            samples_collected += len(targets)

    if hook_handle:
        hook_handle.remove()

    features = np.concatenate(features_list, axis=0)
    labels = np.concatenate(labels_list, axis=0)
    predictions = np.concatenate(preds_list, axis=0)

    return features, labels, predictions


def compute_embeddings(
    features: np.ndarray,
    method: str = "t-SNE",
    perplexity: int = 30,
    n_neighbors: int = 15,
) -> np.ndarray:
    """
    Compute 2D embeddings using dimensionality reduction.

    Args:
        features: (N, D) feature matrix
        method: "t-SNE", "UMAP", or "PCA"
        perplexity: t-SNE perplexity
        n_neighbors: UMAP n_neighbors

    Returns:
        (N, 2) embedding coordinates
    """
    if method == "t-SNE":
        reducer = TSNE(
            n_components=2,
            perplexity=min(perplexity, len(features) - 1),
            random_state=42,
            max_iter=1000,
        )
        return reducer.fit_transform(features)

    if method == "UMAP":
        try:
            import umap

            reducer = umap.UMAP(
                n_components=2,
                n_neighbors=min(n_neighbors, len(features) - 1),
                random_state=42,
            )
            return reducer.fit_transform(features)
        except ImportError as err:
            raise ImportError(
                "umap-learn not installed. Run: pip install umap-learn"
            ) from err

    if method == "PCA":
        reducer = PCA(n_components=2, random_state=42)
        return reducer.fit_transform(features)

    raise ValueError(f"Unknown method: {method}")


def compute_clustering_metrics(embeddings: np.ndarray, labels: np.ndarray) -> dict:
    """Compute clustering quality metrics."""
    try:
        silhouette = silhouette_score(embeddings, labels)
        davies_bouldin = davies_bouldin_score(embeddings, labels)
    except Exception:
        silhouette = 0.0
        davies_bouldin = 0.0

    return {
        "silhouette": silhouette,
        "davies_bouldin": davies_bouldin,
    }
