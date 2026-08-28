# Page 4: Training Configuration

## Why This Page Exists
**Purpose:** Configure training hyperparameters (optimizer, learning rate, regularization). Validate choices BEFORE training starts to prevent wasted time on bad configurations. Embedded monitoring shows live training progress.

---

## Section 1: Optimizer Settings

**Why:** Optimizer choice and learning rate are critical for training success. Wrong values cause divergence or slow convergence.

**Input:** Optimizer type and hyperparameters
**Process:** Configure optimizer
**Output:** Optimizer configuration with sanity checks

```
[st.header] Optimizer Configuration

[st.selectbox] "Optimizer"
    Options: [Adam, AdamW, SGD with Momentum, RMSprop]

[st.slider] "Learning Rate" - log scale, 0.0001 to 0.01, default 0.001
    (show in scientific notation)

[st.expander "Advanced Optimizer Parameters"]
    (Content changes based on optimizer selected)
    If Adam/AdamW:
        [st.slider] "Beta 1" - 0.9 default
        [st.slider] "Beta 2" - 0.999 default
        [st.number_input] "Epsilon" - 1e-7 default
    If SGD:
        [st.slider] "Momentum" - 0.9 default
        [st.checkbox] "Nesterov" - True default
```

**Visualization:**
- Learning rate range indicator:
```
[Too Low] ← 0.0001 ... [Recommended] 0.001 ... 0.01 → [Too High]
```
- Optimizer comparison card:
  | Optimizer | Speed | Stability | Memory | Best For |
  |-----------|-------|-----------|--------|----------|
  | Adam | Fast | Good | High | General purpose |
  | SGD | Slower | Very stable | Low | Large datasets |

**Measurement:**
- Warn if LR > 0.01 (likely too high)
- Warn if LR < 0.00001 (likely too low)
- Suggest LR based on batch size and model size

---

## Section 2: Learning Rate Scheduler

**Why:** LR scheduling improves convergence and final accuracy by reducing LR when loss plateaus.

**Input:** Scheduler type and parameters
**Process:** Configure scheduler
**Output:** Scheduler configuration

```
[st.header] Learning Rate Scheduling

[st.radio] "Strategy"
    Options:
        - Constant (no scheduling)
        - ReduceLROnPlateau
        - Cosine Annealing
        - Step Decay
        - Exponential Decay

[st.expander "Scheduler Parameters"] (content changes per strategy)
    If ReduceLROnPlateau:
        [st.slider] "Reduction Factor" - 0.1-0.9, default 0.5
        [st.slider] "Patience" - 3-20 epochs, default 5
        [st.number_input] "Min LR" - 1e-7 default
    If Cosine Annealing:
        [st.slider] "T_max" - 10-100, default 50
        [st.number_input] "Eta_min" - 0 default
```

**Visualization:**
- LR schedule preview graph:
```
Learning Rate over Epochs (simulated)
Y-axis: LR (log scale)
X-axis: Epoch
Shows projected LR curve based on selected strategy
```

**Measurement:**
- Estimated LR at epochs: 10, 25, 50, 100
- Warn if LR drops below 1e-7 (too small to learn)

---

## Section 3: Training Parameters

**Why:** Batch size and epochs determine training duration and stability. Early validation prevents bad choices.

**Input:** Batch size, max epochs
**Process:** Calculate training iterations
**Output:** Training plan with time estimate

```
[st.header] Training Settings

[st.slider] "Max Epochs" - 10-200, default 100
[st.selectbox] "Batch Size" - 16, 32, 64, 128 (default 32)
[st.checkbox] "Shuffle Training Data" - True default
```

**Visualization:**
- Training plan summary:
```
Total Training Samples: 6,537
Batch Size: 32
Iterations per Epoch: 205
Total Iterations: 20,500 (100 epochs)
Estimated Training Time: 3.5 hours (on GPU)
```
- Batch size trade-off chart:
  | Batch Size | Iterations/Epoch | Speed | Memory | Generalization |
  |------------|------------------|-------|--------|----------------|
  | 16 | 408 | Slower | Low | Better |
  | 32 | 204 | Medium | Medium | Good |
  | 64 | 102 | Faster | High | Good |
  | 128 | 51 | Fastest | Very High | Worse |

**Measurement:**
- Iterations per epoch
- Total training iterations
- Time estimate based on: (iterations × time_per_iteration)
- Warn if batch size > GPU memory can handle
- Warn if epochs < 10 (may underfit)

---

## Section 4: Regularization

**Why:** Prevent overfitting. Shows current dropout configuration from model page.

**Input:** Weight decay lambda
**Process:** Configure L2 regularization
**Output:** Regularization configuration

```
[st.header] Regularization

[st.checkbox] "L2 Weight Decay"
    - If checked: [st.slider] "Lambda" - 0.0001-0.01, default 0.0001

[st.info] "Dropout configured in Model Architecture"
    Dropout rates: Conv layers {x}%, Dense layers {y}%
    [st.button] "Go back to modify"
```

**Visualization:**
- Regularization summary card:
```
Active Regularization Techniques:
- Dropout (Conv): 0.25
- Dropout (Dense): 0.5
- L2 Weight Decay: 0.0001
- Data Augmentation: Light
```

**Measurement:**
- Total regularization strength estimate
- Warn if no regularization enabled (high overfit risk)

---

## Section 5: Class Imbalance Handling

**Why:** Handle imbalanced classes (some malware families have more samples). Critical for fair evaluation.

**Input:** Imbalance strategy
**Process:** Calculate class weights
**Output:** Class weight configuration

```
[st.header] Class Imbalance Strategy

[st.radio] "Method"
    Options:
        - Auto Class Weights (recommended)
        - Focal Loss
        - No Adjustment

[st.expander "Class Distribution"]
    [st.plotly_chart] Bar chart showing class imbalance
    [st.dataframe] Table with class counts and suggested weights
```

**Visualization:**
- Bar chart: samples per class (highlighting imbalance)
- Table:
  | Class | Count | Weight | Effect |
  |-------|-------|--------|--------|
  | Allaple | 1,591 | 0.37 | Underweight |
  | VB.AT | 408 | 1.44 | Overweight |

**Measurement:**
- Imbalance ratio: max/min class count
- Class weights calculated: total_samples / (num_classes × class_count)
- Warn if imbalance ratio > 10 (severe)

---

## Section 6: Callbacks & Early Stopping

**Why:** Stop training automatically when not improving. Save best model. Log metrics for analysis.

**Input:** Callback configurations
**Process:** Configure callbacks
**Output:** Callback configuration

```
[st.header] Training Callbacks

[st.checkbox] "Early Stopping" - True default
    [st.slider] "Patience" - 5-30 epochs, default 10
    [st.number_input] "Min Delta" - 0.0001 default

[st.checkbox] "Model Checkpointing" - True default
    [st.radio] "Save Best By" - [Val Loss, Val Accuracy]

[st.checkbox] "TensorBoard Logging" - False default
```

**Visualization:**
- Callback timeline diagram:
```
Epoch 0 ────────────────────────── Epoch 100
          │          │          │
    Checkpoint   Checkpoint   Early Stop
    (val loss    (val loss    (no improvement
     improved)    improved)    for 10 epochs)
```

**Measurement:**
- Checkpoint storage estimate (model size × max checkpoints)
- Early stopping probability based on patience

---

## Section 7: Experiment Metadata & Start Training

**Why:** Name experiment for tracking. Show final configuration summary. Start training with embedded monitoring.

**Input:** Experiment name and description
**Process:** Aggregate all configs, start training
**Output:** Training starts, embedded monitor appears below

```
[st.header] Experiment Details

[st.text_input] "Experiment Name"
    - Auto-generated: {activation}_{model_type}_{dataset}_{timestamp}
    - User can edit

[st.text_area] "Description (optional)"
    Placeholder: "Testing Mish activation on baseline CNN with MalImg dataset"

[st.multiselect] "Tags"
    Options: [mish, relu, swish, baseline, transfer-learning, malimg, experiment]
    - User can add custom tags

[st.divider]

[st.form "start_training_form"]
    [st.info] "Training Configuration Summary"
        Dataset: MalImg (9,339 samples, 25 classes)
        Model: Custom CNN (2.4M params)
        Epochs: 100 | Batch: 32 | LR: 0.001
        Optimizer: Adam | Scheduler: ReduceLROnPlateau

    [st.warning] "Training will take approximately 3-4 hours on GPU"

    [st.form_submit_button] "START TRAINING" (large, primary button)
        - Saves all config to st.session_state.training_config
        - Initializes training state
        - Shows training monitor below (embedded)
```

**Visualization:**
- Complete configuration JSON tree
- Summary metrics card
- Resource requirements card (GPU memory, disk space)

**Measurement:**
- Configuration completeness check (all required fields set)
- Compatibility validation:
  - Dataset config matches model config
  - Batch size fits in memory
  - All paths exist
- Final sanity checks before starting

---

## Embedded Training Monitor (appears after START clicked)

**Why:** Live feedback during training. Catch problems early (divergence, overfitting).

**See page_5_monitor.md for full details**

Key elements embedded here:
- Live loss/accuracy metrics
- Training progress bar
- Live charts (auto-refresh every 2s)
- Stop/Pause buttons
