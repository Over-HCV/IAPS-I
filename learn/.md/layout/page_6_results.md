# Page 6: Results & Evaluation

## Why This Page Exists
**Purpose:** Comprehensive evaluation of trained model on test set. Understand model performance, identify weaknesses, compare with other experiments. This is the PRIMARY validation page, but NOT the only one (previous pages had intermediate checks).

**Note:** This page appears automatically when training completes, or user can select from completed experiments list.

---

## Section 1: Experiment Summary

**Why:** Identify which experiment these results belong to. Track training metadata.

**Input:** Completed experiment metadata
**Process:** Load experiment info from storage
**Output:** Summary card with key info

```
[st.header] Experiment Results

[st.success] "Training Complete!"

[st.columns 2]
    col1:
        [st.metric] "Experiment ID" - exp_001_mish_cnn_malimg
        [st.metric] "Duration" - 3h 42m
        [st.metric] "Completed At" - 2025-01-20 15:45:23
    col2:
        [st.metric] "Best Epoch" - 47/100
        [st.metric] "Early Stopped At" - Epoch 57
        [st.metric] "Final LR" - 0.000125
```

**Visualization:**
- Experiment info card
- Timeline showing: Start → Best Model (epoch 47) → Early Stop (epoch 57) → End

**Measurement:**
- Total training time
- Best epoch (lowest val loss)
- Whether early stopping triggered
- Final learning rate

---

## Section 2: Final Test Metrics

**Why:** Single-number summary of model performance. Compare across experiments.

**Input:** Model predictions on test set
**Process:** Calculate classification metrics
**Output:** Metric cards

```
[st.header] Test Set Performance

[st.columns 4]
    col1: [st.metric] "Accuracy" - 94.25%
    col2: [st.metric] "Precision (macro)" - 93.87%
    col3: [st.metric] "Recall (macro)" - 93.92%
    col4: [st.metric] "F1-Score (macro)" - 93.89%
```

**Visualization:**
- Large metric cards (color-coded: green >90%, yellow 70-90%, red <70%)
- Comparison with previous experiments (if available):
  ```
  This Experiment: 94.25%
  Previous Best: 92.10%  (↑ 2.15%)
  ```

**Measurement:**
- **Accuracy:** Overall correctness (true predictions / total)
- **Precision:** Of predicted positives, how many correct (avoid false alarms)
- **Recall:** Of actual positives, how many found (avoid missing malware)
- **F1-Score:** Harmonic mean of precision/recall (balanced metric)
- Macro vs weighted averaging explained in tooltip

---

## Section 3: Training History

**Why:** Review full training trajectory. Verify convergence and proper training dynamics.

**Input:** Training history logs
**Process:** Plot final curves (non-updating)
**Output:** Tabbed charts

```
[st.header] Training Curves

[st.tabs] ["Loss", "Accuracy", "Learning Rate"]
    Tab 1: [st.plotly_chart] Loss curves (final, non-updating)
    Tab 2: [st.plotly_chart] Accuracy curves
    Tab 3: [st.plotly_chart] LR schedule
```

**Visualization:**
- Tab 1: Train/val loss over epochs (dual line chart)
- Tab 2: Train/val accuracy over epochs
- Tab 3: Learning rate schedule with reduction markers

**Measurement:**
- Final train/val loss gap (overfitting indicator)
- Epochs until convergence (when val loss stopped improving)
- Number of LR reductions
- Training stability (variance in last 10 epochs)

---

## Section 4: Confusion Matrix

**Why:** See which classes the model confuses. Identify specific weaknesses.

**Input:** True labels vs predicted labels
**Process:** Build confusion matrix
**Output:** Interactive heatmap

```
[st.header] Confusion Matrix

[st.columns 2]
    col1: [st.radio] "Normalize" - [None, True (by row), Pred (by col)]
    col2: [st.selectbox] "Colormap" - [Blues, Viridis, RdYlGn]

[st.plotly_chart] Interactive confusion matrix heatmap
    - Hover shows: True={X}, Pred={Y}, Count={Z}, %={W}
    - Click to highlight row/column
    - Zoomable

[st.expander "Most Confused Class Pairs"]
    [st.dataframe] Table showing:
        True Label | Predicted As | Count | Percentage
        VB         | Alureon      | 23    | 12.3%
        Rbot       | Bifrose      | 18    | 9.8%
        ...
```

**Visualization:**
- Heatmap: rows = true labels, columns = predicted
- Diagonal = correct predictions (bright color)
- Off-diagonal = mistakes (darker colors)
- Normalization options:
  - None: Raw counts
  - By row: Shows recall per class
  - By column: Shows precision per class

**Measurement:**
- Per-class accuracy (diagonal values)
- Most confused pairs (largest off-diagonal values)
- Error rate per class
- Symmetry of confusion (is VB→Alureon == Alureon→VB?)

---

## Section 5: Per-Class Performance

**Why:** Detailed breakdown by malware family. Identify which families are hardest to classify.

**Input:** Per-class metrics from classification report
**Process:** Calculate precision/recall/f1 per class
**Output:** Interactive table and bar chart

```
[st.header] Classification Report

[st.selectbox] "Sort By" - [Class Name, F1-Score, Precision, Recall, Support]

[st.dataframe] Interactive classification report
    Columns: Class | Precision | Recall | F1-Score | Support
    Last rows: Macro Avg, Weighted Avg
    Color-coded by performance (green=high, red=low)

[st.plotly_chart] Bar chart of F1-Scores by class
    X: Class names
    Y: F1-Score
    Color gradient by score
```

**Visualization:**
- Sortable dataframe with conditional formatting
- Bar chart sorted by F1-score (worst to best)
- Highlight classes with F1 < 0.8 (problematic)

**Measurement:**
- Per-class precision, recall, F1-score
- Support (number of samples per class in test set)
- **Key insight:** Which classes have low performance?
- **Root cause:** Low support (few samples) or inherent difficulty?

---

## Section 6: ROC Curves

**Why:** Evaluate classification performance at different decision thresholds. Measure discriminative ability.

**Input:** Model output probabilities + true labels
**Process:** Calculate ROC curves (One-vs-Rest)
**Output:** Multi-line ROC chart + AUC table

```
[st.header] ROC Analysis (One-vs-Rest)

[st.multiselect] "Select Classes to Display"
    - [All classes + "Select All" + "Top 5" + "Bottom 5"]

[st.plotly_chart] ROC curves
    - One line per selected class
    - Diagonal reference line (random classifier)
    - Legend with AUC scores
    - Toggle visibility by clicking legend

[st.dataframe] AUC Scores Summary
    Class | AUC Score | Interpretation
    Alureon | 0.987 | Excellent
    VB      | 0.972 | Excellent
    ...
    Macro Avg | 0.964 | Excellent
```

**Visualization:**
- ROC curves: False Positive Rate (X) vs True Positive Rate (Y)
- Diagonal line = random guess (AUC = 0.5)
- Curves closer to top-left = better (AUC → 1.0)
- Color-coded by class

**Measurement:**
- **AUC (Area Under Curve):** Probability model ranks random positive higher than random negative
  - 1.0 = Perfect
  - 0.9-1.0 = Excellent
  - 0.8-0.9 = Good
  - 0.7-0.8 = Fair
  - <0.7 = Poor
- Macro average AUC across all classes
- Which classes have lowest AUC (hardest to separate)?

---

## Section 7: Export Results

**Why:** Save results for reporting, comparison, or external analysis.

**Input:** All results and configurations
**Process:** Generate export files
**Output:** Downloadable files

```
[st.header] Export & Save

[st.columns 3]
    col1: [st.download_button] "Download PDF Report"
    col2: [st.download_button] "Download Metrics (CSV)"
    col3: [st.download_button] "Download Model (.pt)"

[st.download_button] "Download Full Config (JSON)"
    - Includes all hyperparameters, dataset config, model architecture
```

**Visualization:**
- Download button grid
- File size estimates shown

**Measurement:**
- Generate files:
  - PDF: Full report with all charts + tables
  - CSV: Metrics table for spreadsheet analysis
  - Model: Trained weights (.pt for PyTorch)
  - Config: JSON with all experiment settings

---

## Experiment Comparison (Optional Section)

**Why:** Compare this experiment with previous ones to track progress.

**Input:** Multiple experiment results
**Process:** Load and compare metrics
**Output:** Comparison table and charts

```
[st.expander "Compare with Other Experiments"]
    [st.dataframe] Comparison table
        Experiment | Activation | Accuracy | F1-Score | Training Time
        exp_001 | ReLU | 91.2% | 90.8% | 4.2h
        exp_002 | Mish | 94.3% | 93.9% | 4.5h  ← Current
        exp_003 | Swish | 93.1% | 92.7% | 4.3h

    [st.plotly_chart] Multi-line accuracy curves (overlay multiple experiments)
```

**Visualization:**
- Table highlighting current experiment (bold/colored row)
- Superimposed training curves from multiple experiments
- Bar chart: final accuracies across experiments

**Measurement:**
- Best experiment so far (by accuracy/F1)
- Improvement over baseline (first experiment)
- Which hyperparameter changes had biggest impact?
