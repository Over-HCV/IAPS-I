"""
PyTorch CNN Builder
Builds CNN models from layer_stack configuration using PyTorch
"""

from typing import Any

from models.base import BaseModel
import torch
import torch.nn as nn


class CustomCNNBuilder(BaseModel):
    """Build custom CNN architecture from layer_stack configuration"""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize CNN builder

        Args:
            config: Model configuration with cnn_config containing layer_stack
        """
        super().__init__(config)
        self.cnn_config = config.get("cnn_config", {})
        self.num_classes = config.get("num_classes", 10)

    def build(self) -> nn.Module:
        """Build CNN model from configuration"""
        if not self.validate_config():
            raise ValueError("Invalid model configuration")

        model = CustomCNN(
            layers=self.cnn_config.get("layers", []), num_classes=self.num_classes
        )

        self.model = model
        return model

    def get_parameters_count(self) -> tuple[int, int]:
        """Get parameter counts"""
        if self.model is None:
            self.model = self.build()

        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(
            p.numel() for p in self.model.parameters() if p.requires_grad
        )

        return total_params, trainable_params

    def validate_config(self) -> bool:
        """Validate CNN configuration"""
        if not super().validate_config():
            return False

        if "cnn_config" not in self.config:
            return False

        layers = self.cnn_config.get("layers", [])
        if not layers:
            return False

        has_conv = any(layer["type"] == "Conv2D" for layer in layers)
        has_transition = any(
            layer["type"] in ["Flatten", "GlobalAvgPool"] for layer in layers
        )
        has_dense = any(layer["type"] == "Dense" for layer in layers)

        return has_conv and has_transition and has_dense


class CustomCNN(nn.Module):
    """Custom CNN model built from layer_stack configuration"""

    ACTIVATION_MAP = {
        "relu": nn.ReLU(inplace=True),
        "leaky_relu": nn.LeakyReLU(0.1, inplace=True),
        "gelu": nn.GELU(),
        "swish": nn.SiLU(inplace=True),
        "none": nn.Identity(),
    }

    def __init__(
        self,
        layers: list[dict[str, Any]],
        num_classes: int,
        input_channels: int = 3,
        input_size: int = 224,
    ):
        """
        Initialize custom CNN from layer stack

        Args:
            layers: List of layer configurations from layer_stack
            num_classes: Number of output classes
            input_channels: Number of input channels (3 for RGB)
            input_size: Input image size (assumes square images)
        """
        super().__init__()

        self.layers_config = layers
        self.num_classes = num_classes

        # Build all layers
        self.feature_layers = nn.ModuleList()
        self.classifier_layers = nn.ModuleList()

        current_channels = input_channels
        current_spatial = input_size
        in_classifier = False
        flatten_features = 0

        for layer_config in layers:
            layer_type = layer_config["type"]
            params = layer_config.get("params", {})

            if layer_type == "Conv2D":
                layer, current_channels = self._build_conv2d(current_channels, params)
                self.feature_layers.append(layer)

            elif layer_type == "MaxPooling2D":
                pool_size = params.get("pool_size", 2)
                layer = nn.MaxPool2d(kernel_size=pool_size, stride=pool_size)
                current_spatial = current_spatial // pool_size
                self.feature_layers.append(layer)

            elif layer_type == "AveragePooling2D":
                pool_size = params.get("pool_size", 2)
                layer = nn.AvgPool2d(kernel_size=pool_size, stride=pool_size)
                current_spatial = current_spatial // pool_size
                self.feature_layers.append(layer)

            elif layer_type == "BatchNorm":
                layer = nn.BatchNorm2d(current_channels)
                self.feature_layers.append(layer)

            elif layer_type == "Dropout":
                rate = params.get("rate", 0.25)
                if in_classifier:
                    layer = nn.Dropout(rate)
                    self.classifier_layers.append(layer)
                else:
                    layer = nn.Dropout2d(rate)
                    self.feature_layers.append(layer)

            elif layer_type == "Flatten":
                flatten_features = current_channels * current_spatial * current_spatial
                in_classifier = True

            elif layer_type == "GlobalAvgPool":
                flatten_features = current_channels
                in_classifier = True

            elif layer_type == "Dense":
                if flatten_features == 0:
                    raise ValueError(
                        "Dense layer requires Flatten or GlobalAvgPool before it"
                    )

                units = params.get("units", 256)
                activation = params.get("activation", "relu")

                layer = nn.Linear(flatten_features, units)
                self.classifier_layers.append(layer)
                self.classifier_layers.append(self._get_activation(activation))

                flatten_features = units

        # Add final output layer
        if flatten_features == 0:
            raise ValueError("Model needs Flatten or GlobalAvgPool before output layer")

        self.output_layer = nn.Linear(flatten_features, num_classes)

        # Track if we use GlobalAvgPool or Flatten
        self.use_global_pool = any(layer["type"] == "GlobalAvgPool" for layer in layers)

    def _build_conv2d(
        self, in_channels: int, params: dict[str, Any]
    ) -> tuple[nn.Sequential, int]:
        """Build a Conv2D layer with activation"""
        filters = params.get("filters", 32)
        kernel_size = params.get("kernel_size", 3)
        activation = params.get("activation", "relu")
        padding_mode = params.get("padding", "same")

        padding = kernel_size // 2 if padding_mode == "same" else 0

        layers = [
            nn.Conv2d(in_channels, filters, kernel_size=kernel_size, padding=padding),
            self._get_activation(activation),
        ]

        return nn.Sequential(*layers), filters

    def _get_activation(self, activation: str) -> nn.Module:
        """Get activation function by name"""
        if activation in self.ACTIVATION_MAP:
            act = self.ACTIVATION_MAP[activation]
            if isinstance(act, (nn.ReLU, nn.LeakyReLU, nn.SiLU)):
                return type(act)(inplace=True)
            return type(act)()
        return nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass

        Args:
            x: Input tensor of shape (batch, channels, height, width)

        Returns:
            Output logits of shape (batch, num_classes)
        """
        # Apply feature extraction layers
        for layer in self.feature_layers:
            x = layer(x)

        # Apply transition (flatten or global pool)
        if self.use_global_pool:
            x = torch.mean(x, dim=[2, 3])
        else:
            x = torch.flatten(x, 1)

        # Apply classifier layers
        for layer in self.classifier_layers:
            x = layer(x)

        # Output layer
        x = self.output_layer(x)

        return x

    def get_feature_extractor(self) -> nn.Sequential:
        """Get the feature extraction part of the model"""
        return nn.Sequential(*self.feature_layers)
