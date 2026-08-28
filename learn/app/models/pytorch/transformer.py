"""
Vision Transformer (ViT) Implementation
Custom Vision Transformer for image classification
"""

import math
from typing import Any, Dict, Tuple

from models.base import BaseModel
import torch
import torch.nn as nn
import torch.nn.functional as F


class TransformerBuilder(BaseModel):
    """Build Vision Transformer models"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize transformer builder

        Args:
            config: Model configuration with transformer_config
        """
        super().__init__(config)
        self.transformer_config = config.get("transformer_config", {})
        self.num_classes = config.get("num_classes", 10)

    def build(self) -> nn.Module:
        """Build Vision Transformer model"""
        if not self.validate_config():
            raise ValueError("Invalid model configuration")

        model = VisionTransformer(
            image_size=224,  # Default image size
            patch_size=self.transformer_config.get("patch_size", 16),
            num_classes=self.num_classes,
            embed_dim=self.transformer_config.get("embed_dim", 768),
            depth=self.transformer_config.get("depth", 12),
            num_heads=self.transformer_config.get("num_heads", 12),
            mlp_ratio=self.transformer_config.get("mlp_ratio", 4.0),
            dropout=self.transformer_config.get("dropout", 0.1),
            in_channels=3,  # RGB images
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
        """Validate transformer configuration"""
        if not super().validate_config():
            return False

        if "transformer_config" not in self.config:
            return False

        return True


class PatchEmbedding(nn.Module):
    """Convert image to patches and embed them"""

    def __init__(
        self,
        image_size: int = 224,
        patch_size: int = 16,
        in_channels: int = 3,
        embed_dim: int = 768,
    ):
        super().__init__()
        self.image_size = image_size
        self.patch_size = patch_size
        self.num_patches = (image_size // patch_size) ** 2

        # Use convolution to extract and embed patches
        self.proj = nn.Conv2d(
            in_channels, embed_dim, kernel_size=patch_size, stride=patch_size
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input image tensor (B, C, H, W)

        Returns:
            Patch embeddings (B, num_patches, embed_dim)
        """
        B, C, H, W = x.shape
        assert H == self.image_size and W == self.image_size, (
            f"Input image size ({H}x{W}) doesn't match expected size ({self.image_size}x{self.image_size})"
        )

        # (B, C, H, W) -> (B, embed_dim, H/P, W/P)
        x = self.proj(x)

        # (B, embed_dim, H/P, W/P) -> (B, embed_dim, num_patches)
        x = x.flatten(2)

        # (B, embed_dim, num_patches) -> (B, num_patches, embed_dim)
        x = x.transpose(1, 2)

        return x


class MultiHeadAttention(nn.Module):
    """Multi-Head Self-Attention module"""

    def __init__(self, embed_dim: int, num_heads: int, dropout: float = 0.0):
        super().__init__()
        assert embed_dim % num_heads == 0

        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim**-0.5

        self.qkv = nn.Linear(embed_dim, embed_dim * 3)
        self.attn_drop = nn.Dropout(dropout)
        self.proj = nn.Linear(embed_dim, embed_dim)
        self.proj_drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor (B, N, embed_dim)

        Returns:
            Output tensor (B, N, embed_dim)
        """
        B, N, C = x.shape

        # Generate Q, K, V
        qkv = (
            self.qkv(x)
            .reshape(B, N, 3, self.num_heads, self.head_dim)
            .permute(2, 0, 3, 1, 4)
        )
        q, k, v = qkv[0], qkv[1], qkv[2]  # Each is (B, num_heads, N, head_dim)

        # Attention scores
        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = attn.softmax(dim=-1)
        attn = self.attn_drop(attn)

        # Apply attention to values
        x = (attn @ v).transpose(1, 2).reshape(B, N, C)

        # Output projection
        x = self.proj(x)
        x = self.proj_drop(x)

        return x


class MLP(nn.Module):
    """Feed-forward MLP block"""

    def __init__(
        self,
        in_features: int,
        hidden_features: int = None,
        out_features: int = None,
        dropout: float = 0.0,
    ):
        super().__init__()
        out_features = out_features or in_features
        hidden_features = hidden_features or in_features

        self.fc1 = nn.Linear(in_features, hidden_features)
        self.act = nn.GELU()
        self.fc2 = nn.Linear(hidden_features, out_features)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.fc1(x)
        x = self.act(x)
        x = self.drop(x)
        x = self.fc2(x)
        x = self.drop(x)
        return x


class TransformerBlock(nn.Module):
    """Single Transformer block"""

    def __init__(
        self,
        embed_dim: int,
        num_heads: int,
        mlp_ratio: float = 4.0,
        dropout: float = 0.0,
    ):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn = MultiHeadAttention(embed_dim, num_heads, dropout)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.mlp = MLP(
            in_features=embed_dim,
            hidden_features=int(embed_dim * mlp_ratio),
            dropout=dropout,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Attention with residual
        x = x + self.attn(self.norm1(x))
        # MLP with residual
        x = x + self.mlp(self.norm2(x))
        return x


class VisionTransformer(nn.Module):
    """Vision Transformer (ViT) for image classification"""

    def __init__(
        self,
        image_size: int = 224,
        patch_size: int = 16,
        num_classes: int = 1000,
        embed_dim: int = 768,
        depth: int = 12,
        num_heads: int = 12,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1,
        in_channels: int = 3,
    ):
        """
        Initialize Vision Transformer

        Args:
            image_size: Input image size
            patch_size: Patch size for patch embedding
            num_classes: Number of output classes
            embed_dim: Embedding dimension
            depth: Number of transformer blocks
            num_heads: Number of attention heads
            mlp_ratio: Ratio of MLP hidden dim to embed_dim
            dropout: Dropout rate
            in_channels: Number of input channels
        """
        super().__init__()

        # Patch embedding
        self.patch_embed = PatchEmbedding(
            image_size=image_size,
            patch_size=patch_size,
            in_channels=in_channels,
            embed_dim=embed_dim,
        )
        num_patches = self.patch_embed.num_patches

        # CLS token and position embeddings
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.pos_embed = nn.Parameter(torch.zeros(1, num_patches + 1, embed_dim))
        self.pos_drop = nn.Dropout(dropout)

        # Transformer blocks
        self.blocks = nn.ModuleList(
            [
                TransformerBlock(
                    embed_dim=embed_dim,
                    num_heads=num_heads,
                    mlp_ratio=mlp_ratio,
                    dropout=dropout,
                )
                for _ in range(depth)
            ]
        )

        # Classification head
        self.norm = nn.LayerNorm(embed_dim)
        self.head = nn.Linear(embed_dim, num_classes)

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize weights"""
        # Initialize position embeddings
        nn.init.trunc_normal_(self.pos_embed, std=0.02)
        nn.init.trunc_normal_(self.cls_token, std=0.02)

        # Initialize linear layers and layer norms
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.trunc_normal_(m.weight, std=0.02)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.LayerNorm):
                nn.init.constant_(m.bias, 0)
                nn.init.constant_(m.weight, 1.0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass

        Args:
            x: Input images (B, C, H, W)

        Returns:
            Class logits (B, num_classes)
        """
        B = x.shape[0]

        # Patch embedding
        x = self.patch_embed(x)  # (B, num_patches, embed_dim)

        # Add CLS token
        cls_tokens = self.cls_token.expand(B, -1, -1)  # (B, 1, embed_dim)
        x = torch.cat((cls_tokens, x), dim=1)  # (B, num_patches + 1, embed_dim)

        # Add position embeddings
        x = x + self.pos_embed
        x = self.pos_drop(x)

        # Apply transformer blocks
        for block in self.blocks:
            x = block(x)

        # Normalize
        x = self.norm(x)

        # Extract CLS token and classify
        cls_output = x[:, 0]  # (B, embed_dim)
        x = self.head(cls_output)  # (B, num_classes)

        return x

    def get_attention_maps(self, x: torch.Tensor) -> list:
        """Get attention maps from all transformer blocks (for visualization)"""
        attention_maps = []
        B = x.shape[0]

        # Patch embedding
        x = self.patch_embed(x)

        # Add CLS token
        cls_tokens = self.cls_token.expand(B, -1, -1)
        x = torch.cat((cls_tokens, x), dim=1)

        # Add position embeddings
        x = x + self.pos_embed

        # Get attention from each block
        for block in self.blocks:
            # This would require modifying blocks to return attention
            # For now, just pass through
            x = block(x)

        return attention_maps
