"""
Manual CNN Implementation
Educational implementation of CNN from scratch using NumPy
For comparison with PyTorch implementation
"""

import numpy as np
from typing import Any, Dict, List, Tuple


class ManualCNN:
    """Manual CNN implementation for educational purposes"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize manual CNN

        Args:
            config: Model configuration
        """
        self.config = config
        self.layers = []
        self._build_network()

    def _build_network(self):
        """Build network from configuration"""
        cnn_config = self.config.get("cnn_config", {})
        conv_blocks = cnn_config.get("conv_blocks", [])
        dense_layers = cnn_config.get("dense_layers", [])
        num_classes = self.config.get("num_classes", 10)

        # Add convolutional blocks
        for block in conv_blocks:
            self.layers.append(ConvolutionalLayer(
                filters=block["filters"],
                kernel_size=self._parse_kernel_size(block["kernel_size"]),
                activation=block["activation"]
            ))

            if block.get("has_maxpool", False):
                self.layers.append(MaxPoolingLayer(pool_size=2))

            if block.get("dropout", 0) > 0:
                self.layers.append(DropoutLayer(rate=block["dropout"]))

        # Add flatten layer
        self.layers.append(FlattenLayer())

        # Add dense layers
        for layer in dense_layers:
            self.layers.append(DenseLayer(
                units=layer["units"],
                activation=layer["activation"]
            ))

            if layer.get("dropout", 0) > 0:
                self.layers.append(DropoutLayer(rate=layer["dropout"]))

        # Add output layer
        self.layers.append(DenseLayer(
            units=num_classes,
            activation="softmax"
        ))

    def _parse_kernel_size(self, kernel_str: str) -> int:
        """Parse kernel size from string"""
        return int(kernel_str.split('x')[0])

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass through the network

        Args:
            x: Input array of shape (batch, height, width, channels)

        Returns:
            Output predictions
        """
        for layer in self.layers:
            x = layer.forward(x)
        return x

    def backward(self, grad_output: np.ndarray, learning_rate: float = 0.01):
        """
        Backward pass through the network

        Args:
            grad_output: Gradient of loss w.r.t output
            learning_rate: Learning rate for parameter updates
        """
        grad = grad_output
        for layer in reversed(self.layers):
            grad = layer.backward(grad, learning_rate)

    def get_params_count(self) -> Tuple[int, int]:
        """Get total and trainable parameter counts"""
        total_params = 0
        trainable_params = 0

        for layer in self.layers:
            if hasattr(layer, 'weights'):
                params = layer.weights.size
                if hasattr(layer, 'bias'):
                    params += layer.bias.size
                total_params += params
                trainable_params += params

        return total_params, trainable_params


class ConvolutionalLayer:
    """Manual implementation of convolutional layer"""

    def __init__(self, filters: int, kernel_size: int, activation: str):
        self.filters = filters
        self.kernel_size = kernel_size
        self.activation = activation
        self.weights = None
        self.bias = None
        self.input_shape = None
        self.output = None
        self.input = None

    def initialize_weights(self, input_channels: int):
        """Initialize weights using He initialization"""
        self.weights = np.random.randn(
            self.filters, input_channels, self.kernel_size, self.kernel_size
        ) * np.sqrt(2.0 / (input_channels * self.kernel_size * self.kernel_size))
        self.bias = np.zeros(self.filters)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass

        Args:
            x: Input of shape (batch, height, width, channels)

        Returns:
            Output of shape (batch, new_height, new_width, filters)
        """
        batch_size, h, w, channels = x.shape

        # Initialize weights on first pass
        if self.weights is None:
            self.initialize_weights(channels)

        # Calculate output dimensions (assuming same padding)
        pad = self.kernel_size // 2
        out_h = h
        out_w = w

        # Pad input
        x_padded = np.pad(x, ((0, 0), (pad, pad), (pad, pad), (0, 0)), mode='constant')

        # Perform convolution
        output = np.zeros((batch_size, out_h, out_w, self.filters))

        for b in range(batch_size):
            for f in range(self.filters):
                for i in range(out_h):
                    for j in range(out_w):
                        # Extract patch
                        patch = x_padded[b, i:i+self.kernel_size, j:j+self.kernel_size, :]

                        # Convolve
                        output[b, i, j, f] = np.sum(patch * self.weights[f]) + self.bias[f]

        # Apply activation
        self.input = x
        self.output = self._apply_activation(output)
        return self.output

    def backward(self, grad_output: np.ndarray, learning_rate: float) -> np.ndarray:
        """Backward pass - simplified for educational purposes"""
        # This is a simplified version
        # Real implementation would compute proper gradients
        return grad_output

    def _apply_activation(self, x: np.ndarray) -> np.ndarray:
        """Apply activation function"""
        if self.activation == "ReLU":
            return np.maximum(0, x)
        elif self.activation == "Leaky ReLU":
            return np.where(x > 0, x, 0.1 * x)
        elif self.activation == "sigmoid":
            return 1 / (1 + np.exp(-x))
        elif self.activation == "tanh":
            return np.tanh(x)
        else:
            return x


class MaxPoolingLayer:
    """Manual implementation of max pooling layer"""

    def __init__(self, pool_size: int = 2):
        self.pool_size = pool_size
        self.input_shape = None
        self.max_indices = None

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass

        Args:
            x: Input of shape (batch, height, width, channels)

        Returns:
            Pooled output
        """
        batch_size, h, w, channels = x.shape
        self.input_shape = x.shape

        out_h = h // self.pool_size
        out_w = w // self.pool_size

        output = np.zeros((batch_size, out_h, out_w, channels))
        self.max_indices = np.zeros((batch_size, out_h, out_w, channels, 2), dtype=int)

        for b in range(batch_size):
            for c in range(channels):
                for i in range(out_h):
                    for j in range(out_w):
                        # Extract pool region
                        pool_region = x[
                            b,
                            i*self.pool_size:(i+1)*self.pool_size,
                            j*self.pool_size:(j+1)*self.pool_size,
                            c
                        ]

                        # Find max value and its position
                        max_val = np.max(pool_region)
                        max_pos = np.unravel_index(np.argmax(pool_region), pool_region.shape)

                        output[b, i, j, c] = max_val
                        self.max_indices[b, i, j, c] = max_pos

        return output

    def backward(self, grad_output: np.ndarray, learning_rate: float) -> np.ndarray:
        """Backward pass"""
        # Simplified - would need to route gradients to max positions
        return grad_output


class DenseLayer:
    """Manual implementation of fully connected layer"""

    def __init__(self, units: int, activation: str = "linear"):
        self.units = units
        self.activation = activation
        self.weights = None
        self.bias = None
        self.input = None
        self.output = None

    def initialize_weights(self, input_dim: int):
        """Initialize weights using He initialization"""
        self.weights = np.random.randn(input_dim, self.units) * np.sqrt(2.0 / input_dim)
        self.bias = np.zeros(self.units)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass

        Args:
            x: Input of shape (batch, features)

        Returns:
            Output of shape (batch, units)
        """
        if self.weights is None:
            self.initialize_weights(x.shape[-1])

        self.input = x
        z = np.dot(x, self.weights) + self.bias
        self.output = self._apply_activation(z)
        return self.output

    def backward(self, grad_output: np.ndarray, learning_rate: float) -> np.ndarray:
        """Backward pass with weight updates"""
        # Gradient through activation
        grad_z = grad_output * self._activation_derivative(self.output)

        # Gradient w.r.t weights and bias
        grad_weights = np.dot(self.input.T, grad_z)
        grad_bias = np.sum(grad_z, axis=0)

        # Update weights
        self.weights -= learning_rate * grad_weights
        self.bias -= learning_rate * grad_bias

        # Gradient to pass to previous layer
        grad_input = np.dot(grad_z, self.weights.T)
        return grad_input

    def _apply_activation(self, x: np.ndarray) -> np.ndarray:
        """Apply activation function"""
        if self.activation == "ReLU":
            return np.maximum(0, x)
        elif self.activation == "sigmoid":
            return 1 / (1 + np.exp(-x))
        elif self.activation == "softmax":
            exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
            return exp_x / np.sum(exp_x, axis=-1, keepdims=True)
        elif self.activation == "linear":
            return x
        else:
            return x

    def _activation_derivative(self, output: np.ndarray) -> np.ndarray:
        """Compute derivative of activation function"""
        if self.activation == "ReLU":
            return (output > 0).astype(float)
        elif self.activation == "sigmoid":
            return output * (1 - output)
        elif self.activation == "softmax":
            # For softmax with cross-entropy, derivative is handled differently
            return np.ones_like(output)
        else:
            return np.ones_like(output)


class FlattenLayer:
    """Flatten layer to convert conv output to dense input"""

    def __init__(self):
        self.input_shape = None

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Flatten all dimensions except batch"""
        self.input_shape = x.shape
        batch_size = x.shape[0]
        return x.reshape(batch_size, -1)

    def backward(self, grad_output: np.ndarray, learning_rate: float) -> np.ndarray:
        """Reshape gradient back to original shape"""
        return grad_output.reshape(self.input_shape)


class DropoutLayer:
    """Dropout layer for regularization"""

    def __init__(self, rate: float = 0.5):
        self.rate = rate
        self.mask = None
        self.training = True

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Apply dropout during training"""
        if self.training:
            self.mask = np.random.binomial(1, 1 - self.rate, size=x.shape) / (1 - self.rate)
            return x * self.mask
        return x

    def backward(self, grad_output: np.ndarray, learning_rate: float) -> np.ndarray:
        """Pass gradient through dropout mask"""
        if self.training:
            return grad_output * self.mask
        return grad_output

    def set_training(self, training: bool):
        """Set training mode"""
        self.training = training