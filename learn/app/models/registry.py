"""
Model family registry

Each family declares which kinds of data and which tasks it can handle. Pages
ask the registry what is available instead of hardcoding a list, so supporting a
new architecture means adding an entry here rather than editing the Model page,
the training worker and the evaluator.

Kept free of Streamlit imports so the background training worker can use it.
"""

from dataclasses import dataclass
from typing import Any

from models.base import BaseModel
from models.pytorch.cnn_builder import CustomCNNBuilder
from models.pytorch.mlp import MLPBuilder
from models.pytorch.transfer import TransferLearningBuilder
from models.pytorch.transformer import TransformerBuilder

IMAGE_FOLDER = "image_folder"
TABULAR = "tabular"

CLASSIFICATION = "classification"
REGRESSION = "regression"

# Trainer backend. Epoch-based PyTorch training is the only one today; tree
# models will register a fit-based backend alongside it.
TORCH = "torch"


@dataclass(frozen=True)
class ModelFamily:
    """One selectable architecture and what it can be applied to"""

    name: str
    description: str
    data_kinds: tuple[str, ...]
    tasks: tuple[str, ...]
    backend: str
    builder: type[BaseModel]
    config_key: str


FAMILIES: tuple[ModelFamily, ...] = (
    ModelFamily(
        name="Custom CNN",
        description=(
            "Convolutional network built from scratch. Full control over layer "
            "depth, filter counts and regularization."
        ),
        data_kinds=(IMAGE_FOLDER,),
        tasks=(CLASSIFICATION,),
        backend=TORCH,
        builder=CustomCNNBuilder,
        config_key="cnn_config",
    ),
    ModelFamily(
        name="Transformer",
        description=(
            "Vision Transformer. Strong on large datasets, demanding to train."
        ),
        data_kinds=(IMAGE_FOLDER,),
        tasks=(CLASSIFICATION,),
        backend=TORCH,
        builder=TransformerBuilder,
        config_key="transformer_config",
    ),
    ModelFamily(
        name="Transfer Learning",
        description=(
            "Pre-trained backbone (ResNet, EfficientNet, VGG) fine-tuned on your "
            "data. Usually the fastest route to a good result."
        ),
        data_kinds=(IMAGE_FOLDER,),
        tasks=(CLASSIFICATION,),
        backend=TORCH,
        builder=TransferLearningBuilder,
        config_key="transfer_config",
    ),
    ModelFamily(
        name="Tabular MLP",
        description=(
            "Dense network over encoded feature columns. Trains through the same "
            "engine as the image models, so live monitoring and checkpoints work."
        ),
        data_kinds=(TABULAR,),
        tasks=(CLASSIFICATION,),
        backend=TORCH,
        builder=MLPBuilder,
        config_key="mlp_config",
    ),
)

_BY_NAME = {family.name: family for family in FAMILIES}


def get_family(name: str) -> ModelFamily | None:
    """Look up a model family by its display name"""
    return _BY_NAME.get(name)


def families_for(data_kind: str, task: str = CLASSIFICATION) -> list[ModelFamily]:
    """Every family that can be trained on this kind of data for this task"""
    return [
        family
        for family in FAMILIES
        if data_kind in family.data_kinds and task in family.tasks
    ]


def build_model(model_config: dict[str, Any]):
    """Build a model from a saved model config"""
    name = model_config.get("model_type")
    family = get_family(name)

    if family is None:
        raise ValueError(
            f"Unknown model type: {name}. Known types: {sorted(_BY_NAME)}"
        )

    return family.builder(model_config).build()
