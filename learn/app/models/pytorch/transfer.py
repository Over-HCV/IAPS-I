"""
Transfer Learning Models
Pre-trained model fine-tuning with PyTorch
"""

from typing import Any, Dict, Tuple

from models.base import BaseModel
import torch
import torch.nn as nn
import torchvision.models as models


class TransferLearningBuilder(BaseModel):
    """Build transfer learning models from pre-trained backbones"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize transfer learning builder

        Args:
            config: Model configuration with transfer_config
        """
        super().__init__(config)
        self.transfer_config = config.get("transfer_config", {})
        self.num_classes = config.get("num_classes", 10)

    def build(self) -> nn.Module:
        """Build transfer learning model"""
        if not self.validate_config():
            raise ValueError("Invalid model configuration")

        base_model_name = self.transfer_config["base_model"]
        weights = self.transfer_config.get("weights", "ImageNet")
        strategy = self.transfer_config.get("strategy", "Feature Extraction")

        # Create the model
        model = TransferModel(
            base_model_name=base_model_name,
            num_classes=self.num_classes,
            weights=weights,
            strategy=strategy,
            unfreeze_layers=self.transfer_config.get("unfreeze_layers", 0),
            global_pooling=self.transfer_config.get("global_pooling", True),
            add_dense=self.transfer_config.get("add_dense", False),
            dense_units=self.transfer_config.get("dense_units", 512),
            dropout=self.transfer_config.get("dropout", 0.5),
        )

        self.model = model
        return model

    def get_parameters_count(self) -> Tuple[int, int]:
        """Get parameter counts"""
        if self.model is None:
            self.model = self.build()

        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(
            p.numel() for p in self.model.parameters() if p.requires_grad
        )

        return total_params, trainable_params

    def validate_config(self) -> bool:
        """Validate transfer learning configuration"""
        if not super().validate_config():
            return False

        if "transfer_config" not in self.config:
            return False

        required_fields = ["base_model", "strategy"]
        for field in required_fields:
            if field not in self.transfer_config:
                return False

        return True


class TransferModel(nn.Module):
    """Transfer learning model with configurable fine-tuning"""

    def __init__(
        self,
        base_model_name: str,
        num_classes: int,
        weights: str = "ImageNet",
        strategy: str = "Feature Extraction",
        unfreeze_layers: int = 0,
        global_pooling: bool = True,
        add_dense: bool = False,
        dense_units: int = 512,
        dropout: float = 0.5,
    ):
        """
        Initialize transfer learning model

        Args:
            base_model_name: Name of pre-trained model
            num_classes: Number of output classes
            weights: "ImageNet" or "Random"
            strategy: "Feature Extraction", "Partial Fine-tuning", or "Full Fine-tuning"
            unfreeze_layers: Number of layers to unfreeze (for partial fine-tuning)
            global_pooling: Whether to use global average pooling
            add_dense: Whether to add an extra dense layer
            dense_units: Number of units in extra dense layer
            dropout: Dropout rate before final layer
        """
        super().__init__()

        # Load pre-trained model
        self.base_model = self._load_base_model(base_model_name, weights)

        # Get the number of features from the base model
        in_features = self._get_in_features(base_model_name)

        # Remove the original classifier
        self._remove_classifier(base_model_name)

        # Apply freezing strategy
        self._apply_freezing_strategy(strategy, unfreeze_layers)

        # Build custom classifier head
        classifier_layers = []

        if global_pooling:
            self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        else:
            self.global_pool = None

        if add_dense:
            classifier_layers.extend(
                [
                    nn.Linear(in_features, dense_units),
                    nn.ReLU(inplace=True),
                    nn.Dropout(dropout),
                    nn.Linear(dense_units, num_classes),
                ]
            )
        else:
            classifier_layers.extend(
                [nn.Dropout(dropout), nn.Linear(in_features, num_classes)]
            )

        self.classifier = nn.Sequential(*classifier_layers)

    def _load_base_model(self, model_name: str, weights: str) -> nn.Module:
        """Load pre-trained base model"""
        use_pretrained = weights == "ImageNet"

        model_map = {
            "VGG16": lambda: models.vgg16(pretrained=use_pretrained),
            "VGG19": lambda: models.vgg19(pretrained=use_pretrained),
            "ResNet50": lambda: models.resnet50(pretrained=use_pretrained),
            "ResNet101": lambda: models.resnet101(pretrained=use_pretrained),
            "InceptionV3": lambda: models.inception_v3(
                pretrained=use_pretrained, aux_logits=False
            ),
            "EfficientNetB0": lambda: models.efficientnet_b0(pretrained=use_pretrained),
        }

        if model_name not in model_map:
            raise ValueError(f"Unknown model: {model_name}")

        return model_map[model_name]()

    def _get_in_features(self, model_name: str) -> int:
        """Get number of input features for classifier"""
        if "VGG" in model_name:
            return self.base_model.classifier[0].in_features
        elif "ResNet" in model_name:
            return self.base_model.fc.in_features
        elif "Inception" in model_name:
            return self.base_model.fc.in_features
        elif "EfficientNet" in model_name:
            return self.base_model.classifier[1].in_features
        else:
            return 2048  # Default

    def _remove_classifier(self, model_name: str):
        """Remove the original classifier from base model"""
        if "VGG" in model_name:
            # Keep features, remove classifier
            self.base_model.classifier = nn.Identity()
        elif "ResNet" in model_name:
            self.base_model.fc = nn.Identity()
        elif "Inception" in model_name:
            self.base_model.fc = nn.Identity()
        elif "EfficientNet" in model_name:
            self.base_model.classifier = nn.Identity()

    def _apply_freezing_strategy(self, strategy: str, unfreeze_layers: int):
        """Apply layer freezing based on strategy"""
        if strategy == "Feature Extraction":
            # Freeze all base model parameters
            for param in self.base_model.parameters():
                param.requires_grad = False

        elif strategy == "Partial Fine-tuning":
            # Freeze all first
            for param in self.base_model.parameters():
                param.requires_grad = False

            # Unfreeze last N layers
            all_layers = list(self.base_model.children())
            layers_to_unfreeze = (
                all_layers[-unfreeze_layers:] if unfreeze_layers > 0 else []
            )

            for layer in layers_to_unfreeze:
                for param in layer.parameters():
                    param.requires_grad = True

        elif strategy == "Full Fine-tuning":
            # All parameters are trainable (default)
            pass

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass

        Args:
            x: Input tensor of shape (batch, channels, height, width)

        Returns:
            Output logits of shape (batch, num_classes)
        """
        # Extract features
        features = self.base_model(x)

        # Apply global pooling if needed
        if self.global_pool is not None and len(features.shape) == 4:
            features = self.global_pool(features)
            features = torch.flatten(features, 1)
        elif len(features.shape) == 4:
            # Flatten if needed
            features = torch.flatten(features, 1)

        # Apply classifier
        output = self.classifier(features)

        return output

    def get_trainable_layers(self) -> list:
        """Get list of trainable layer names"""
        trainable_layers = []
        for name, param in self.named_parameters():
            if param.requires_grad:
                trainable_layers.append(name)
        return trainable_layers
