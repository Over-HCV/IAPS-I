"""
Shared Configuration Constants
BFS Level: Define constants, no implementation
"""

from pathlib import Path

# Dataset paths
DATASET_ROOT = Path("dataset")

# Default training parameters
DEFAULT_TRAIN_SPLIT = 70
DEFAULT_VAL_SPLIT = 15
DEFAULT_TEST_SPLIT = 15
DEFAULT_RANDOM_SEED = 72

# Default preprocessing
DEFAULT_TARGET_SIZE = (224, 224)
DEFAULT_NORMALIZATION = "[0,1]"
DEFAULT_COLOR_MODE = "Grayscale"

# Default augmentation presets
AUGMENTATION_PRESETS = {
    "None": {},
    "Light": {
        "rotation": 10,
        "horizontal_flip": 0.5,
        "brightness": 0.1
    },
    "Moderate": {
        "rotation": 20,
        "horizontal_flip": 0.5,
        "vertical_flip": 0.3,
        "brightness": 0.2,
        "contrast": 0.2
    },
    "Heavy": {
        "rotation": 30,
        "horizontal_flip": 0.5,
        "vertical_flip": 0.5,
        "brightness": 0.3,
        "contrast": 0.3,
        "gaussian_noise": 0.05
    }
}

# Model architecture options
ACTIVATION_FUNCTIONS = ["ReLU", "Mish", "Swish", "GELU", "Leaky ReLU"]
KERNEL_SIZES = ["3x3", "5x5", "7x7"]
FILTER_OPTIONS = [32, 64, 128, 256, 512]
DENSE_UNIT_OPTIONS = [64, 128, 256, 512, 1024]

# Transfer learning models
PRETRAINED_MODELS = [
    "VGG16",
    "VGG19",
    "ResNet50",
    "ResNet101",
    "InceptionV3",
    "EfficientNetB0"
]

# Training defaults
DEFAULT_LEARNING_RATE = 0.001
DEFAULT_BATCH_SIZE = 32
DEFAULT_MAX_EPOCHS = 100
DEFAULT_OPTIMIZER = "Adam"

OPTIMIZER_OPTIONS = ["Adam", "AdamW", "SGD with Momentum", "RMSprop"]
LR_SCHEDULER_OPTIONS = [
    "Constant",
    "ReduceLROnPlateau",
    "Cosine Annealing",
    "Step Decay",
    "Exponential Decay"
]

# Class imbalance methods
CLASS_IMBALANCE_METHODS = [
    "Auto Class Weights (recommended)",
    "Focal Loss",
    "No Adjustment"
]

# Storage paths
STORAGE_ROOT = Path("storage")
SESSIONS_DIR = STORAGE_ROOT / "sessions"
MODELS_DIR = STORAGE_ROOT / "models"
RESULTS_DIR = STORAGE_ROOT / "results"
CHECKPOINTS_DIR = STORAGE_ROOT / "checkpoints"

# Ensure directories exist (will be called on app startup)
def init_storage_dirs():
    """Create storage directories if they don't exist"""
    for dir_path in [SESSIONS_DIR, MODELS_DIR, RESULTS_DIR, CHECKPOINTS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
