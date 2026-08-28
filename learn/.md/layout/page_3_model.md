# Page 3: Model Configuration

## Why This Page Exists
**Purpose:** Design the neural network architecture. Allows experimentation with custom CNNs (activation functions, layer configs) or transfer learning. Validates architecture BEFORE training (parameter count, memory requirements).

---

## Section 1: Model Type Selection

**Why:** Choose between building custom CNN from scratch vs using pre-trained models

**Input:** User's choice of approach
**Process:** Toggle between Custom CNN or Transfer Learning UI
**Output:** Model type selection stored in state

```
[st.header] Model Architecture

[st.radio] "Model Type"
    Options: [Custom CNN, Transfer Learning]
    - Changes what sections appear below
```

**Visualization:**
- Info cards comparing Custom CNN vs Transfer Learning:
  | Aspect | Custom CNN | Transfer Learning |
  |--------|-----------|-------------------|
  | Training Time | Longer | Shorter |
  | Data Required | More | Less |
  | Flexibility | Full control | Limited |
  | Best For | Experimentation | Quick results |

**Measurement:** None (selection only)

---

## IF Custom CNN Selected:

### Section 2: Convolutional Layers

**Why:** Define feature extraction layers. Number of blocks and filters determines model capacity and what visual patterns it can learn.

**Input:** Layer configurations (filters, kernel size, activation)
**Process:** Build convolutional block configs
**Output:** List of conv blocks stored in state

```
[st.header] Convolutional Layers

For each block (dynamically added):
    [st.expander f"Convolutional Block {i}"] (expanded by default for first block)
        [st.columns 2]
            col1:
                [st.slider] "Number of Filters" - 32, 64, 128, 256, 512
                [st.selectbox] "Kernel Size" - 3x3, 5x5, 7x7
                [st.selectbox] "Activation" - ReLU, Mish, Swish, GELU, Leaky ReLU
                    (with tooltip showing recommendation from activation.md)
            col2:
                [st.checkbox] "Add Second Conv Layer" - False default
                [st.checkbox] "MaxPooling 2x2" - True default
                [st.slider] "Dropout" - 0.0-0.5, default 0.25

        [st.button] "Remove Block" (if more than 1 block exists)

[st.button] "+ Add Convolutional Block" (max 7 blocks)
```

**Visualization:**
- Live architecture diagram updating as blocks are added:
```
Input (224x224x1)
    ↓
Conv2D (32 filters, 3x3, ReLU)
    ↓
MaxPool2D (2x2) → Output: 112x112x32
    ↓
Conv2D (64 filters, 3x3, ReLU)
    ↓
MaxPool2D (2x2) → Output: 56x56x64
    ↓
...
```

**Measurement:**
- Parameter count per block
- Output spatial dimensions after each block
- Warn if output size becomes too small (e.g., < 4x4)
- Memory estimate for feature maps

---

### Section 3: Fully Connected Layers

**Why:** Classification head that maps features to class probabilities. Layer sizes affect model capacity and overfitting risk.

**Input:** Dense layer configurations
**Process:** Build dense layer configs
**Output:** List of dense layers stored in state

```
[st.header] Dense Layers

For each dense layer (dynamically added):
    [st.expander f"Dense Layer {i}"] (expanded by default)
        [st.slider] "Units" - 64, 128, 256, 512, 1024
        [st.selectbox] "Activation" - ReLU, Mish, Swish, GELU
        [st.slider] "Dropout" - 0.0-0.7, default 0.5

        [st.button] "Remove Layer" (if more than 1 layer)

[st.button] "+ Add Dense Layer" (max 5 layers)
```

**Visualization:**
- Layer flow diagram:
```
Flatten
    ↓
Dense (512 units, ReLU)
Dropout (0.5)
    ↓
Dense (256 units, ReLU)
Dropout (0.5)
    ↓
Output (25 units, Softmax)
```

**Measurement:**
- Parameter count per dense layer
- Total dense layer parameters
- Warn if too many parameters (overfitting risk)

---

### Section 4: Output Layer (Auto)

**Why:** Output layer must match number of classes from dataset. Auto-configured to prevent errors.

**Input:** num_classes from dataset config
**Process:** Auto-generate output layer
**Output:** Output layer with softmax activation

```
[st.header] Output Layer

[st.info] Auto-configured based on dataset
    Units: {num_classes} (from dataset config)
    Activation: Softmax
```

**Visualization:**
- Output layer card showing:
  - Number of output neurons = number of classes
  - Activation function (Softmax for multi-class)

**Measurement:**
- Verify num_classes matches dataset metadata

---

## IF Transfer Learning Selected:

### Section 2: Pre-trained Model Selection

**Why:** Choose base architecture. Different models have different trade-offs (accuracy vs speed vs memory).

**Input:** Pre-trained model selection
**Process:** Load model metadata
**Output:** Base model configuration

```
[st.header] Pre-trained Model

[st.radio] "Select Base Model"
    Options: [VGG16, VGG19, ResNet50, ResNet101, InceptionV3, EfficientNetB0]
    - Show info card with params, input size, description

[st.radio] "Weights"
    Options: [ImageNet (recommended), Random (train from scratch)]
```

**Visualization:**
- Model comparison table:
  | Model | Params | Input Size | Depth | Best For |
  |-------|--------|------------|-------|----------|
  | VGG16 | 138M | 224x224 | 16 | Simple, reliable |
  | ResNet50 | 25M | 224x224 | 50 | Good balance |
  | InceptionV3 | 24M | 299x299 | 48 | Efficiency |

**Measurement:**
- Total parameters in base model
- Required input size (warn if doesn't match preprocessing config)
- Memory requirement estimate

---

### Section 3: Fine-tuning Strategy

**Why:** Decide how much of pre-trained model to retrain. Affects training time and performance.

**Input:** Fine-tuning approach
**Process:** Configure layer freezing
**Output:** Trainable layer configuration

```
[st.header] Fine-tuning Configuration

[st.radio] "Strategy"
    Options:
        - Feature Extraction (freeze all base layers)
        - Partial Fine-tuning (trainable last N layers)
        - Full Fine-tuning (all layers trainable, low LR)

[st.slider] "Layers to Unfreeze" - 0 to {total_layers}
    (only shown if Partial Fine-tuning selected)
```

**Visualization:**
- Layer diagram showing frozen (gray) vs trainable (green) layers:
```
[FROZEN] Block 1 (conv layers 1-3)
[FROZEN] Block 2 (conv layers 4-7)
[FROZEN] Block 3 (conv layers 8-13)
[TRAINABLE] Block 4 (conv layers 14-16)
[TRAINABLE] Classification Head
```

**Measurement:**
- Number of frozen parameters
- Number of trainable parameters
- Ratio of trainable/total parameters
- Training speed estimate based on trainable params

---

### Section 4: Custom Top Layers

**Why:** Replace pre-trained model's original classification head with custom one for malware classification.

**Input:** Classification head configuration
**Process:** Define custom layers on top of base model
**Output:** Custom head configuration

```
[st.header] Classification Head

[st.checkbox] "Global Average Pooling" - True default
[st.checkbox] "Add Dense Layer"
    - If checked, show [st.slider] "Units" - 256, 512, 1024
[st.slider] "Dropout" - 0.0-0.7, default 0.5
```

**Visualization:**
- Classification head diagram:
```
Base Model Output
    ↓
Global Average Pooling
    ↓
Dense (512 units, ReLU)  [Optional]
Dropout (0.5)
    ↓
Output (25 units, Softmax)
```

**Measurement:**
- Parameters added by custom head
- Total trainable parameters

---

## Section 5: Architecture Summary (Both CNN & Transfer Learning)

**Why:** Final validation before training. Ensure model fits in memory and matches expectations.

**Input:** Complete model configuration
**Process:** Build model, count parameters
**Output:** Model summary visualization

```
[st.header] Model Architecture Summary

[st.text] Text representation of model architecture
    Input (224, 224, 1)
         ↓
    Conv2D (32 filters, 3x3, ReLU)
         ↓
    MaxPool2D (2x2)
         ↓
    ...
         ↓
    Dense (25, Softmax)

[st.columns 3]
    col1: [st.metric] "Total Parameters" - 2,456,789
    col2: [st.metric] "Trainable Parameters" - 2,456,789
    col3: [st.metric] "Estimated Memory" - ~38 MB
```

**Visualization:**
- Full architecture diagram (text-based layer listing)
- Parameter breakdown pie chart (conv vs dense vs other)
- Memory usage bar chart (weights vs activations vs gradients)

**Measurement:**
- Total parameters
- Trainable vs frozen parameters
- Memory estimate (weights + activations + gradients)
- Warn if memory > available GPU RAM
- FLOPs (floating point operations) estimate
- Inference time estimate (based on FLOPs)

---

## Section 6: Save & Export (Optional)

**Why:** Allow users to save architecture for reuse or external use

**Input:** Model architecture
**Process:** Generate Python code
**Output:** Downloadable model definition

```
[st.expander "Advanced: Export Model Code"]
    [st.code] Python code to recreate this architecture
    [st.download_button] "Download model.py"
```

**Visualization:**
- Syntax-highlighted Python code

**Measurement:** None

---

## Section 7: Continue to Training

**Why:** Checkpoint before moving to training configuration

**Input:** Complete model configuration
**Process:** Validate and save config
**Output:** Navigate to training page

```
[st.divider]

[st.success] "Model Configuration Complete"

[st.button] "Next: Training Configuration"
    - Saves to st.session_state.model_config
    - Navigates to Training page
```

**Visualization:**
- Quick summary card with key metrics

**Measurement:**
- Configuration completeness check
- Compatibility check with dataset config (input size, num_classes)
