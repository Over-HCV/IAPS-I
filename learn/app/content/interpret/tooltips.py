"""
Tooltips for model interpretability page.
Centralized tooltip text for visualization methods and controls.
"""

# Tab-level tooltips
TAB_TOOLTIPS = {
    "architecture": (
        "View model architecture summary, layer details, and parameter counts. "
        "Useful for understanding model capacity and structure."
    ),
    "misclassifications": (
        "Analyze which samples the model gets wrong. "
        "Identify patterns in errors to understand model weaknesses."
    ),
    "embeddings": (
        "Visualize learned feature representations in 2D/3D. "
        "Well-separated clusters indicate good class discrimination."
    ),
    "gradcam": (
        "Gradient-weighted Class Activation Mapping. "
        "Highlights image regions most important for the prediction."
    ),
    "advanced": (
        "Additional interpretability methods: LIME explanations, "
        "activation maps, and learned filter visualizations."
    ),
}

# Grad-CAM tooltips
GRADCAM_TOOLTIPS = {
    "method": (
        "Grad-CAM computes gradients of the target class with respect to "
        "feature maps, highlighting discriminative regions. "
        "Works with any CNN architecture."
    ),
    "target_layer": (
        "Convolutional layer to visualize. "
        "Earlier layers: low-level features (edges, textures). "
        "Later layers: high-level concepts (objects, patterns)."
    ),
    "target_class": (
        "Class to explain. Default: predicted class. "
        "Can select other classes to see what would activate them."
    ),
    "opacity": (
        "Heatmap overlay transparency. "
        "Higher = more visible heatmap, less visible original image."
    ),
    "heatmap": (
        "Warm colors (red/yellow): high importance regions. "
        "Cool colors (blue): low importance regions. "
        "Model focuses on warm regions for classification."
    ),
}

# LIME tooltips
LIME_TOOLTIPS = {
    "method": (
        "Local Interpretable Model-agnostic Explanations. "
        "Segments image into superpixels, tests which regions affect prediction. "
        "Model-agnostic: works with any classifier."
    ),
    "num_samples": (
        "Number of perturbed images to generate. "
        "More samples = more accurate explanation but slower. "
        "Typical: 100-500."
    ),
    "num_features": (
        "Number of superpixels to highlight in explanation. "
        "More features = more detailed but noisier visualization."
    ),
    "superpixels": (
        "Image segments identified by LIME. "
        "LIME tests which segments are important by hiding/showing them."
    ),
    "positive_mask": (
        "Green regions: support the predicted class. "
        "Hiding these regions decreases prediction confidence."
    ),
    "negative_mask": (
        "Red regions: contradict the predicted class. "
        "These regions push the model toward other classes."
    ),
    "segment_importance": (
        "Importance score for each superpixel. "
        "Positive = supports prediction. Negative = contradicts prediction."
    ),
}

# Activation maps tooltips
ACTIVATION_TOOLTIPS = {
    "method": (
        "Visualizes what each convolutional filter detects. "
        "Shows filter responses to the input image. "
        "Bright areas = strong filter activation."
    ),
    "layer_selection": (
        "Choose which convolutional layer to visualize. "
        "Earlier layers: detect edges, colors, textures. "
        "Later layers: detect complex patterns and shapes."
    ),
    "max_filters": (
        "Number of filter activations to display. "
        "Each filter detects different features."
    ),
    "activation_map": (
        "Grayscale image showing filter response strength. "
        "White = strong activation (feature present). "
        "Black = no activation (feature absent)."
    ),
}

# Filter weights tooltips
FILTER_TOOLTIPS = {
    "method": (
        "Visualizes learned convolutional kernels directly. "
        "Shows what patterns each filter is looking for. "
        "First layer filters are most interpretable."
    ),
    "kernel_visualization": (
        "RGB filters show color patterns learned. "
        "Grayscale shows intensity patterns. "
        "First layer: often edge detectors at various orientations."
    ),
    "filter_shape": (
        "Kernel dimensions: output_channels × input_channels × height × width. "
        "Example: 64×3×3×3 = 64 filters, each 3×3 on 3 input channels (RGB)."
    ),
}

# Embeddings tooltips
EMBEDDINGS_TOOLTIPS = {
    "method_tsne": (
        "t-SNE: Non-linear dimensionality reduction. "
        "Preserves local structure: similar samples stay close. "
        "Good for visualization but not for quantitative analysis."
    ),
    "method_pca": (
        "PCA: Linear dimensionality reduction. "
        "Preserves maximum variance in the data. "
        "Fast and deterministic but may miss non-linear structure."
    ),
    "method_umap": (
        "UMAP: Faster than t-SNE, preserves both local and global structure. "
        "Good balance between speed and quality."
    ),
    "perplexity": (
        "t-SNE parameter controlling neighborhood size. "
        "Low values: focus on local structure. "
        "High values: consider more global structure. "
        "Typical: 5-50."
    ),
    "n_neighbors": (
        "UMAP parameter for local neighborhood size. "
        "More neighbors = more global structure preserved."
    ),
    "silhouette_score": (
        "Measures cluster quality. Range: -1 to 1. "
        "Higher = better separated clusters. "
        ">0.5 = good clustering."
    ),
    "davies_bouldin": (
        "Measures cluster separation. Lower = better. "
        "Ratio of within-cluster scatter to between-cluster separation."
    ),
    "color_by_true": "Color points by ground truth class labels.",
    "color_by_pred": "Color points by model predictions.",
    "color_by_correct": "Color by correct (green) vs incorrect (red) predictions.",
}

# Misclassification tooltips
MISCLASSIFICATION_TOOLTIPS = {
    "confusion_matrix": (
        "Shows prediction vs actual class for all samples. "
        "Diagonal = correct predictions. Off-diagonal = errors. "
        "Darker color = more samples."
    ),
    "error_gallery": (
        "Gallery of misclassified samples. "
        "Shows true label, predicted label, and confidence. "
        "Look for patterns in errors."
    ),
    "class_accuracy": (
        "Per-class accuracy breakdown. "
        "Low accuracy classes may need more training data or augmentation."
    ),
    "error_distribution": (
        "Which classes are most commonly confused. "
        "Helps identify similar-looking malware families."
    ),
}

# Architecture tooltips
ARCHITECTURE_TOOLTIPS = {
    "layer_summary": (
        "Table showing each layer's output shape and parameter count. "
        "Helps understand information flow through the network."
    ),
    "parameter_count": (
        "Total number of learnable parameters. "
        "More parameters = more capacity but higher risk of overfitting."
    ),
    "model_graph": (
        "Visual representation of the network architecture. "
        "Shows layer connections and data flow."
    ),
    "inference_time": (
        "Time to process one image. "
        "Important for deployment and real-time applications."
    ),
}
