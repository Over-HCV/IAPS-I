"""
Base Model Interface
Abstract base class for all model implementations
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple
import torch.nn as nn


class BaseModel(ABC):
    """Abstract base class for model implementations"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize model with configuration

        Args:
            config: Model configuration dictionary
        """
        self.config = config
        self.model = None

    @abstractmethod
    def build(self) -> nn.Module:
        """
        Build and return the model

        Returns:
            PyTorch model (nn.Module)
        """
        pass

    @abstractmethod
    def get_parameters_count(self) -> Tuple[int, int]:
        """
        Get total and trainable parameter counts

        Returns:
            Tuple of (total_params, trainable_params)
        """
        pass

    def get_model_summary(self) -> Dict[str, Any]:
        """
        Get model summary statistics

        Returns:
            Dictionary with model statistics
        """
        if self.model is None:
            self.model = self.build()

        total_params, trainable_params = self.get_parameters_count()

        return {
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "model_type": self.config.get("model_type", "Unknown"),
            "architecture": self.config.get("architecture", "Unknown"),
            "num_classes": self.config.get("num_classes", 0)
        }

    def validate_config(self) -> bool:
        """
        Validate model configuration

        Returns:
            True if configuration is valid
        """
        return "num_classes" in self.config and self.config["num_classes"] > 0