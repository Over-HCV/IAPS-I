# Page 5: Training Monitor (Embedded in Page 4)

## Why This Page Exists
**Purpose:** Real-time training feedback. Catch problems early (loss divergence, overfitting, dead neurons). Monitor training health without waiting for completion. Allows stopping bad runs immediately.

**Note:** This is embedded in Page 4 after "START TRAINING" is clicked, but can also be standalone page for monitoring multiple experiments.

---

## Section 1: Training Status

**Why:** High-level status at a glance. Know what's happening without scrolling.

**Input:** Training process state
**Process:** Monitor training thread/process
**Output:** Live status indicators

```
[st.header] Training in Progress

[st.status] "Training..." (expandable, updated via @st.fragment)
    Current Status: Epoch 15/100
    Estimated Time Remaining: 2h 34m
    GPU Memory: 4.2 / 8.0 GB
```

**Visualization:**
- Status badge (green = training, yellow = paused, red = error)
- Time remaining countdown
- GPU memory bar (horizontal bar showing usage)

**Measurement:**
- Current epoch / total epochs
- Time elapsed
- Time remaining estimate (based on avg epoch time)
- GPU memory usage (torch.cuda.memory_allocated())
- CPU usage
- Disk I/O

---

## Section 2: Progress Bar

**Why:** Visual feedback on training completion. Satisfying to watch progress.

**Input:** Current epoch and batch
**Process:** Calculate percentage complete
**Output:** Progress bar

```
[st.progress] Epoch progress - 15/100 (15%)
[st.text] "Epoch 15/100 - Batch 187/256"
```

**Visualization:**
- Main progress bar: overall training progress (0-100%)
- Sub progress bar: current epoch progress (batches)

**Measurement:**
- Epochs completed / total epochs
- Batches completed in current epoch
- Percentage complete

---

## Section 3: Current Metrics

**Why:** Immediate feedback on training health. Compare train vs val to detect overfitting.

**Input:** Latest epoch metrics
**Process:** Extract from training logs
**Output:** Metric cards with delta indicators

```
[st.columns 4]
    col1: [st.metric] "Train Loss" - 0.3421 (↓ 0.05 from last epoch)
    col2: [st.metric] "Train Acc" - 89.34% (↑ 2.1%)
    col3: [st.metric] "Val Loss" - 0.4156 (↓ 0.03)
    col4: [st.metric] "Val Acc" - 86.72% (↑ 1.8%)
```

**Visualization:**
- Metric cards with delta arrows (green ↑ good, red ↓ bad)
- Color coding: green if improving, yellow if stagnant, red if worsening

**Measurement:**
- Train loss (should decrease)
- Train accuracy (should increase)
- Val loss (should decrease)
- Val accuracy (should increase)
- **Key check:** Train-val gap (if train_acc - val_acc > 10%, overfitting)

---

## Section 4: Live Training Curves

**Why:** Visualize training dynamics. Spot overfitting, underfitting, or divergence immediately.

**Input:** Training history (loss/acc per epoch)
**Process:** Update Plotly charts every 2s
**Output:** Interactive line charts

```
[st.header] Training History

[@st.fragment run_every="2s"] Auto-updating charts

[st.plotly_chart] Training & Validation Loss
    X: Epoch
    Y: Loss
    Lines: Train (blue), Val (red)

[st.plotly_chart] Training & Validation Accuracy
    X: Epoch
    Y: Accuracy (%)
    Lines: Train (blue), Val (red)
```

**Visualization:**
- Dual-line chart: train vs val
- Lines update in real-time as new epochs complete
- Hover shows exact values
- Zoom/pan enabled

**Measurement:**
- Loss convergence rate (how fast loss decreases)
- Accuracy plateau detection (no improvement for N epochs)
- **Overfitting detection:** Val loss starts increasing while train loss decreases
- **Underfitting detection:** Both losses plateau at high values
- **Divergence detection:** Loss suddenly spikes or becomes NaN

---

## Section 5: Learning Rate Schedule

**Why:** Verify LR scheduler is working correctly. See when LR reductions happen.

**Input:** LR history per epoch
**Process:** Track LR changes
**Output:** LR curve with annotations

```
[st.plotly_chart] Learning Rate over Time
    X: Epoch
    Y: Learning Rate (log scale)
    Annotations: When LR was reduced
```

**Visualization:**
- Line chart showing LR over time
- Log scale on Y-axis (LR spans multiple orders of magnitude)
- Vertical markers when LR reduced (e.g., "Epoch 25: LR reduced to 0.0005")

**Measurement:**
- Current LR
- LR reduction events
- Verify LR follows expected schedule

---

## Section 6: Training Logs

**Why:** Detailed text logs for debugging. See exact error messages if training fails.

**Input:** Training process stdout/stderr
**Process:** Stream logs in real-time
**Output:** Scrollable text area

```
[st.expander "Training Logs" collapsed]
    [st.text_area] (read-only, auto-scroll to bottom)
        [15:23:45] Epoch 15/100
        [15:23:47] 187/256 - loss: 0.3421 - acc: 0.8934 - val_loss: 0.4156 - val_acc: 0.8672
        [15:23:50] EarlyStopping: val_loss did not improve
        [15:23:51] ReduceLROnPlateau: Reducing LR to 0.0005
        ...
```

**Visualization:**
- Monospace text area with timestamps
- Color coding: info (white), warning (yellow), error (red)
- Auto-scroll to latest log

**Measurement:**
- Capture warnings and errors
- Count warnings/errors for health score

---

## Section 7: Training Controls

**Why:** Allow user intervention. Stop bad runs early to save time. Save checkpoints manually.

**Input:** User button clicks
**Process:** Send signals to training process
**Output:** Training state changes

```
[st.columns 3]
    col1: [st.button] "Pause Training"
    col2: [st.button] "Stop Training"
    col3: [st.download_button] "Save Checkpoint"

[st.info] "Training will continue in background. You can navigate to other pages."
```

**Visualization:**
- Button states: Pause (yellow), Stop (red), Save (blue)
- Confirmation dialog for Stop button

**Measurement:**
- Track user interventions (pauses, stops)
- Checkpoint save success/failure

---

## Real-time Health Checks (Automated Warnings)

**Why:** Automatically detect common training problems and alert user.

**Measurements that trigger warnings:**

1. **Loss Divergence**
   - Trigger: Loss > 10× initial loss OR Loss = NaN
   - Warning: "Training diverging! Loss exploded. Consider lowering learning rate."

2. **Overfitting**
   - Trigger: (train_loss < val_loss) AND (val_loss increasing for 3 epochs)
   - Warning: "Overfitting detected! Validation loss increasing. Consider more regularization."

3. **Underfitting**
   - Trigger: Both losses plateau > 0.5 for 10 epochs AND accuracy < 70%
   - Warning: "Model underfitting. Consider increasing model capacity or training longer."

4. **Dead Neurons**
   - Trigger: >50% of activations = 0 in any layer
   - Warning: "Dead neurons detected in Layer X. Consider lower LR or different activation."

5. **Vanishing Gradients**
   - Trigger: Gradient norm < 1e-7
   - Warning: "Gradients vanishing. Consider different activation or batch normalization."

6. **Memory Issues**
   - Trigger: GPU memory > 95%
   - Warning: "Low GPU memory. Training may crash. Consider smaller batch size."

**Visualization:**
- Alert banner at top of page (dismissible)
- Alert history in expander
