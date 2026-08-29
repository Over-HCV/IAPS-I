"""
PyTorch MLP Builder
Builds a dense network for tabular feature vectors
"""

from typing import Any

from models.base import BaseModel
import torch.nn as nn

ACTIVATIONS = {
    "ReLU": nn.ReLU,
    "GELU": nn.GELU,
    "Leaky ReLU": nn.LeakyReLU,
    "Mish": nn.Mish,
    "Tanh": nn.Tanh,
}

DEFAULT_HIDDEN_LAYERS = [128, 64]
DEFAULT_ACTIVATION = "ReLU"


class MLPBuilder(BaseModel):
    """Build a multilayer perceptron from mlp_config"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.mlp_config = config.get("mlp_config", {})
        self.num_classes = config.get("num_classes", 2)

    def build(self) -> nn.Module:
        """Build the MLP from configuration"""
        if not self.validate_config():
            raise ValueError("Invalid model configuration")

        input_dim = self.mlp_config.get("input_dim", 0)
        if input_dim <= 0:
            raise ValueError(
                "MLP needs input_dim: save the dataset configuration first so the "
                "encoded feature count is known."
            )

        self.model = MLP(
            input_dim=input_dim,
            hidden_layers=self.mlp_config.get("hidden_layers", DEFAULT_HIDDEN_LAYERS),
            num_classes=self.num_classes,
            activation=self.mlp_config.get("activation", DEFAULT_ACTIVATION),
            dropout=self.mlp_config.get("dropout", 0.0),
            batch_norm=self.mlp_config.get("batch_norm", False),
        )

        return self.model

    def get_parameters_count(self) -> tuple[int, int]:
        """Get total and trainable parameter counts"""
        if self.model is None:
            self.model = self.build()

        total = sum(p.numel() for p in self.model.parameters())
        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)

        return total, trainable


class MLP(nn.Module):
    """Dense network: [Linear -> norm -> activation -> dropout] * n -> Linear"""

    def __init__(
        self,
        input_dim: int,
        hidden_layers: list[int],
        num_classes: int,
        activation: str = DEFAULT_ACTIVATION,
        dropout: float = 0.0,
        batch_norm: bool = False,
    ):
        super().__init__()

        activation_layer = ACTIVATIONS.get(activation, nn.ReLU)

        layers: list[nn.Module] = []
        in_features = input_dim

        for units in hidden_layers:
            layers.append(nn.Linear(in_features, units))

            if batch_norm:
                layers.append(nn.BatchNorm1d(units))

            layers.append(activation_layer())

            if dropout > 0:
                layers.append(nn.Dropout(dropout))

            in_features = units

        layers.append(nn.Linear(in_features, num_classes))

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)
