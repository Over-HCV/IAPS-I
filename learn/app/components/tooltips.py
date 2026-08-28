"""
Tooltips for components.
Centralized tooltip text for sidebar, header, and shared UI elements.
"""

SIDEBAR_TOOLTIPS = {
    "system_resources": (
        "Shows your system's compute capabilities for training neural networks. "
        "CUDA = NVIDIA GPU, MPS = Apple Silicon, CPU = No GPU acceleration."
    ),
    "gpu_memory": (
        "GPU video memory (VRAM). Shows used/total for CUDA devices. "
        "'Unified' means Apple Silicon shares memory with system RAM. "
        "More VRAM allows larger batch sizes and models."
    ),
    "system_ram": (
        "System memory (RAM) usage. Used/Total in GB. "
        "Data loading and preprocessing happen in RAM before GPU transfer."
    ),
    "cpu_info": (
        "CPU cores (C) and threads (T). "
        "More threads improve data loading parallelism (num_workers)."
    ),
    "platform": (
        "Operating system. macOS uses MPS for Apple Silicon, "
        "Linux/Windows typically use CUDA for NVIDIA GPUs."
    ),
    "delete_session": (
        "Permanently delete this session and all its data. "
        "This removes saved models, training history, and configurations."
    ),
}

HEADER_TOOLTIPS = {
    "dataset_status": (
        "Dataset configuration status. "
        "Check = dataset path and classes are configured."
    ),
    "model_status": (
        "Model configuration status. "
        "Check = at least one model architecture is saved in the library."
    ),
    "training_status": (
        "Training completion status. "
        "Check = at least one experiment has finished training."
    ),
    "session_selector": (
        "Switch between saved sessions. "
        "Each session maintains its own dataset, models, and experiments."
    ),
    "new_session": (
        "Create a new session with fresh state. "
        "Current session is automatically saved before switching."
    ),
}
