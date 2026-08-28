"""
Tooltips for results page.
Centralized tooltip text for metrics, charts, and evaluation.
"""

# Overall metrics tooltips
METRICS_TOOLTIPS = {
    "accuracy": (
        "Percentage of correct predictions overall. "
        "Can be misleading for imbalanced datasets - a model predicting "
        "only the majority class can still have high accuracy."
    ),
    "precision": (
        "Of all samples predicted as class X, what fraction actually are X. "
        "High precision = few false positives. "
        "Important when false positives are costly."
    ),
    "recall": (
        "Of all actual class X samples, what fraction were correctly identified. "
        "High recall = few false negatives. "
        "Important when missing positives is costly (e.g., malware detection)."
    ),
    "f1_score": (
        "Harmonic mean of precision and recall. "
        "Balances both metrics. Range: 0-1, higher is better. "
        "More informative than accuracy for imbalanced data."
    ),
    "macro_avg": (
        "Average metric across all classes (unweighted). "
        "Treats all classes equally regardless of size. "
        "Good for evaluating performance on minority classes."
    ),
    "weighted_avg": (
        "Average metric weighted by class frequency. "
        "Reflects overall performance but can hide poor minority class performance."
    ),
    "support": (
        "Number of samples in each class. "
        "Low support = less reliable metrics for that class."
    ),
}

# Confusion matrix tooltips
CONFUSION_MATRIX_TOOLTIPS = {
    "matrix": (
        "Rows = true labels, columns = predictions. "
        "Diagonal cells = correct predictions. "
        "Off-diagonal = errors. Look for patterns in confusion."
    ),
    "true_positive": (
        "Correctly identified as positive. "
        "Model correctly detected the malware family."
    ),
    "false_positive": (
        "Incorrectly identified as positive (Type I error). "
        "Model predicted this class but it was actually another."
    ),
    "false_negative": (
        "Incorrectly identified as negative (Type II error). "
        "Model missed this malware family."
    ),
    "true_negative": (
        "Correctly identified as negative. "
        "Model correctly rejected this class."
    ),
    "normalize": (
        "Normalize by row (true labels) or column (predictions). "
        "Row normalization shows recall per class. "
        "Column normalization shows precision per class."
    ),
}

# Training history tooltips
HISTORY_TOOLTIPS = {
    "loss_curve": (
        "Loss over training epochs. Should decrease over time. "
        "Train loss decreasing but val loss increasing = overfitting."
    ),
    "accuracy_curve": (
        "Accuracy over training epochs. Should increase. "
        "Large gap between train and val = overfitting."
    ),
    "learning_rate_curve": (
        "Learning rate over epochs. Shows scheduler behavior. "
        "Drops indicate scheduled reductions or plateau detection."
    ),
    "best_epoch": (
        "Epoch with best validation performance. "
        "Model checkpoint saved at this epoch."
    ),
    "early_stopping": (
        "Training stopped early due to no improvement. "
        "Prevents overfitting and saves time."
    ),
}

# Per-class performance tooltips
CLASS_PERFORMANCE_TOOLTIPS = {
    "class_accuracy": (
        "Accuracy for each individual class. "
        "Low accuracy may indicate insufficient training data or class similarity."
    ),
    "class_f1": (
        "F1 score per class. Better than accuracy for imbalanced classes. "
        "Low F1 indicates issues with either precision or recall."
    ),
    "precision_recall_curve": (
        "Trade-off between precision and recall at different thresholds. "
        "Area under curve (AUC) summarizes overall performance."
    ),
    "roc_curve": (
        "Receiver Operating Characteristic curve. "
        "Plots true positive rate vs false positive rate. "
        "AUC = 1.0 is perfect, 0.5 is random guessing."
    ),
}

# Model comparison tooltips
COMPARISON_TOOLTIPS = {
    "experiment_comparison": (
        "Compare metrics across different experiments. "
        "Helps identify best model configuration."
    ),
    "statistical_significance": (
        "Whether performance differences are statistically meaningful. "
        "Small differences may be due to random variation."
    ),
    "inference_speed": (
        "Images processed per second. "
        "Important for deployment and real-time applications."
    ),
    "model_size": (
        "Model file size in MB. "
        "Smaller models deploy easier and run faster."
    ),
}

# Export tooltips
EXPORT_TOOLTIPS = {
    "export_model": (
        "Save trained model for deployment. "
        "Includes architecture and learned weights."
    ),
    "export_onnx": (
        "Export to ONNX format for cross-platform deployment. "
        "Runs on many inference engines."
    ),
    "export_torchscript": (
        "Export to TorchScript for optimized inference. "
        "Can run without Python."
    ),
    "export_report": (
        "Generate PDF/HTML report with all metrics and charts. "
        "Good for documentation and sharing results."
    ),
}

# Chart-specific tooltips
CHART_TOOLTIPS = {
    "hover_info": "Hover over data points for detailed values.",
    "zoom": "Click and drag to zoom. Double-click to reset.",
    "legend": "Click legend items to show/hide series.",
    "download": "Use the camera icon to save chart as PNG.",
}
