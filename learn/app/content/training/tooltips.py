"""
Tooltips for training configuration page.
Centralized tooltip text for hyperparameters, optimizers, and training settings.
"""

# Hyperparameter tooltips
HYPERPARAMETER_TOOLTIPS = {
    "epochs": (
        "Number of complete passes through the training dataset. "
        "More epochs = more training time. Use early stopping to prevent overfitting."
    ),
    "batch_size": (
        "Number of samples processed before updating weights. "
        "Larger batches: stable gradients, faster per-epoch, needs more GPU memory. "
        "Smaller batches: noisier gradients, better generalization, slower."
    ),
    "learning_rate": (
        "Step size for weight updates. Critical hyperparameter. "
        "Too high: training diverges. Too low: training stalls. "
        "Common starting point: 0.001 for Adam, 0.01 for SGD."
    ),
    "weight_decay": (
        "L2 regularization penalty on weights. "
        "Prevents weights from growing too large. "
        "Typical values: 1e-4 to 1e-2. Higher = stronger regularization."
    ),
    "momentum": (
        "Accelerates SGD in the relevant direction. "
        "Helps escape local minima and dampens oscillations. "
        "Common value: 0.9."
    ),
    "gradient_clip": (
        "Maximum allowed gradient norm. "
        "Prevents exploding gradients in deep networks. "
        "Set to 0 to disable. Common value: 1.0."
    ),
}

# Optimizer tooltips
OPTIMIZER_TOOLTIPS = {
    "adam": (
        "Adaptive Moment Estimation. Combines momentum and RMSprop. "
        "Self-adjusting learning rates per parameter. "
        "Good default choice, works well out of the box."
    ),
    "adamw": (
        "Adam with decoupled weight decay. "
        "Fixes weight decay behavior in Adam. "
        "Recommended for transformers and modern architectures."
    ),
    "sgd": (
        "Stochastic Gradient Descent with momentum. "
        "Simple but often generalizes better than Adam. "
        "Requires careful learning rate tuning."
    ),
    "rmsprop": (
        "RMSprop adapts learning rate using moving average of squared gradients. "
        "Good for recurrent networks and non-stationary objectives."
    ),
}

# Learning rate scheduler tooltips
SCHEDULER_TOOLTIPS = {
    "none": "Fixed learning rate throughout training.",
    "step": (
        "Reduces learning rate by a factor at fixed intervals. "
        "Simple and predictable. Good baseline scheduler."
    ),
    "cosine": (
        "Smoothly decreases learning rate following a cosine curve. "
        "Reaches minimum at the end of training. "
        "Popular for image classification."
    ),
    "cosine_warmup": (
        "Linear warmup followed by cosine decay. "
        "Warmup prevents early divergence with large learning rates. "
        "Recommended for transformers."
    ),
    "reduce_on_plateau": (
        "Reduces learning rate when validation loss stops improving. "
        "Adaptive: only reduces when needed. "
        "Good for uncertain training dynamics."
    ),
    "one_cycle": (
        "Ramps up then down through a learning rate range. "
        "Can achieve faster convergence and better results. "
        "Requires setting max_lr carefully."
    ),
}

# Scheduler parameter tooltips
SCHEDULER_PARAM_TOOLTIPS = {
    "step_size": "Number of epochs between learning rate reductions.",
    "gamma": "Factor to multiply learning rate by (e.g., 0.1 = divide by 10).",
    "warmup_epochs": "Number of epochs to linearly increase learning rate from 0.",
    "min_lr": "Minimum learning rate floor. Training continues at this rate.",
    "patience": "Epochs to wait before reducing LR if no improvement.",
}

# Early stopping tooltips
EARLY_STOPPING_TOOLTIPS = {
    "enabled": (
        "Stop training when validation loss stops improving. "
        "Prevents overfitting and saves time."
    ),
    "patience": (
        "Number of epochs to wait for improvement before stopping. "
        "Higher patience = more chances for recovery. "
        "Lower patience = faster stopping but may miss improvements."
    ),
    "min_delta": (
        "Minimum change to qualify as an improvement. "
        "Set to 0 for strict improvement checking."
    ),
    "restore_best": (
        "Restore model weights from the best epoch after stopping. "
        "Recommended to ensure you keep the best model."
    ),
}

# Experiment tooltips
EXPERIMENT_TOOLTIPS = {
    "experiment_name": (
        "Unique name for this experiment. "
        "Used to identify saved models and training logs."
    ),
    "model_selection": "Choose a model architecture from your library.",
    "training_config": "Choose a training configuration from your library.",
    "experiment_status": {
        "ready": "Experiment configured, ready to start training.",
        "training": "Training in progress.",
        "paused": "Training paused. Can be resumed.",
        "completed": "Training finished successfully.",
        "failed": "Training failed. Check logs for errors.",
    },
}

# Training monitor tooltips
MONITOR_TOOLTIPS = {
    "loss_chart": (
        "Training and validation loss over epochs. "
        "Decreasing loss = model learning. "
        "Val loss increasing while train decreases = overfitting."
    ),
    "accuracy_chart": (
        "Training and validation accuracy over epochs. "
        "Gap between train and val accuracy indicates overfitting."
    ),
    "learning_rate_chart": (
        "Learning rate over time. "
        "Shows scheduler behavior and any reductions."
    ),
    "epoch_time": (
        "Time per epoch. Useful for estimating total training time."
    ),
    "gpu_utilization": (
        "GPU usage during training. "
        "Low utilization may indicate data loading bottleneck."
    ),
}

# Data loading tooltips
DATA_LOADING_TOOLTIPS = {
    "num_workers": (
        "Number of parallel processes for data loading. "
        "More workers = faster data loading if CPU-bound. "
        "Set to 0 for debugging. Typical: 2-4 × CPU cores."
    ),
    "pin_memory": (
        "Pin data in CPU memory for faster GPU transfer. "
        "Enable when using CUDA. Disable for MPS/CPU."
    ),
    "prefetch_factor": (
        "Number of batches to prefetch per worker. "
        "Higher = more memory usage but smoother training."
    ),
}
