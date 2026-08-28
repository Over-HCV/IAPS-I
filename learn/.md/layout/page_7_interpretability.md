# Page 7: Model Interpretability

## Why This Page Exists
**Purpose:** Understand WHAT the model learned and WHY it makes predictions. Critical for trust and debugging. Visualize learned features, identify model focus areas, analyze misclassifications.

---

## Section 1: Grad-CAM Visualization

**Why:** See which image regions the model focuses on for classification. Verify model uses meaningful patterns, not artifacts.

**Input:** Test sample + trained model
**Process:** Compute Grad-CAM heatmap for target layer
**Output:** Original image + heatmap + overlay

```
[st.header] Grad-CAM: What the Model Sees

[st.file_uploader] "Upload Malware Sample (or pick from test set)"
    - OR [st.selectbox] "Select from test set"

[st.columns 3]
    col1:
        [st.image] Original Image
        [st.caption] True: {family}, Pred: {family}
    col2:
        [st.image] Grad-CAM Heatmap
        [st.caption] Focus regions highlighted
    col3:
        [st.image] Overlay
        [st.caption] Combined view

[st.slider] "Heatmap Opacity" - 0.0-1.0, default 0.4
[st.selectbox] "Target Layer" - [Last Conv, Conv Block 3, Conv Block 2]

[st.expander "Prediction Confidence"]
    [st.dataframe] Top 5 predictions with probabilities
        Rank | Class | Probability | Bar
        1    | Alureon | 98.7% | ████████████████████
        2    | VB      | 1.2%  | █
        ...
```

**Visualization:**
- Three-panel view: Original | Heatmap | Overlay
- Heatmap: Red = high importance, Blue = low importance
- Adjustable opacity slider for overlay

**Measurement:**
- Top-5 prediction probabilities
- Confidence score (max probability)
- Prediction correctness (True == Pred?)
- **Key question:** Does model focus on meaningful features or random noise?

---

## Section 2: t-SNE Embeddings

**Why:** Visualize how model organizes malware families in feature space. Clusters indicate learned similarity.

**Input:** Model embeddings (before final layer) for test set
**Process:** Reduce to 2D using t-SNE/UMAP/PCA
**Output:** Interactive 2D scatter plot

```
[st.header] Feature Space Visualization

[st.radio] "Dimensionality Reduction Method"
    Options: [t-SNE, UMAP, PCA]

[st.columns 2]
    col1: [st.slider] "Perplexity" - 5-50, default 30 (if t-SNE)
    col2: [st.slider] "Samples to Plot" - 100-all, default 1000

[st.radio] "Color Points By"
    Options: [True Family, Predicted Family, Correct/Incorrect]

[st.plotly_chart] Interactive 2D scatter plot
    - Each point = one sample
    - Hover: Sample ID, True class, Pred class, Confidence
    - Click: Show sample image in sidebar
    - Lasso/box select for analysis

[st.columns 2]
    col1: [st.metric] "Silhouette Score" - 0.847 (cluster quality)
    col2: [st.metric] "Davies-Bouldin Index" - 0.423
```

**Visualization:**
- 2D scatter plot with color-coded points
- Points of same family should cluster together
- Misclassified samples highlighted (red border)

**Measurement:**
- **Silhouette Score:** How well-separated clusters are (-1 to 1, higher better)
- **Davies-Bouldin Index:** Cluster separation quality (lower better)
- **Visual patterns:**
  - Tight clusters = model learned distinct representations
  - Overlapping clusters = families are similar or model confused
  - Outliers = anomalous samples or errors

---

## Section 3: Activation Maps

**Why:** See what patterns individual filters detect. Understand hierarchical feature learning.

**Input:** Sample + trained model
**Process:** Extract intermediate activations for each conv layer
**Output:** Grid of activation maps

```
[st.header] Convolutional Filter Activations

[st.selectbox] "Select Sample"
[st.selectbox] "Select Layer" - [Conv2D_1, Conv2D_2, Conv2D_3, ...]

[st.info] "Layer info: {filters} filters, output shape {shape}"

[st.columns 6] Feature maps grid (showing first 18 filters)
    Each cell: [st.image] of activation map + filter index

[st.button] "Show All {N} Filters" - Expands to show all
```

**Visualization:**
- Grid of activation maps (grayscale images)
- Each map shows what one filter detects
- First layers: edges, textures
- Deeper layers: complex patterns

**Measurement:**
- Number of active filters (non-zero activations)
- Average activation strength per filter
- Dead filters (always output zero) count

---

## Section 4: Filter Weights Visualization

**Why:** Visualize learned convolutional kernels. See what patterns filters are looking for.

**Input:** Trained model weights
**Process:** Extract conv layer kernels
**Output:** Grid of kernel heatmaps

```
[st.header] Learned Convolutional Filters

[st.selectbox] "Select Convolutional Layer"

[st.columns 8] Grid of 3x3 kernel weights
    Each cell: Heatmap visualization of kernel

[st.expander "Filter Statistics"]
    [st.dataframe] Per-filter stats
        Filter | Mean | Std | Min | Max | L2 Norm
```

**Visualization:**
- Heatmaps of 3x3 or 5x5 kernels
- Color: Red = positive weights, Blue = negative
- Patterns visible: edge detectors, blur kernels, etc.

**Measurement:**
- Weight statistics per filter
- L2 norm (magnitude of filter)
- Dead filters (all weights ≈ 0)

---

## Section 5: LIME Explanations

**Why:** Local explanations for individual predictions. Which image regions support/oppose the prediction?

**Input:** Sample + trained model
**Process:** Run LIME algorithm (superpixel-based)
**Output:** Segmentation with contribution weights

```
[st.header] LIME: Local Interpretable Explanations

[st.selectbox] "Select Sample"

[st.columns 3]
    col1: [st.image] Original
    col2: [st.image] Superpixels (segmentation)
    col3: [st.image] Explanation (green=support, red=against)

[st.slider] "Number of Superpixels" - 50-500, default 200
[st.slider] "Top Features to Show" - 5-20, default 10

[st.dataframe] Top Contributing Segments
    Segment ID | Weight | Effect
    #142 | +0.347 | Strongly supports prediction
    #089 | +0.289 | Supports prediction
    #201 | -0.145 | Against prediction

[st.button] "Recompute LIME" (if parameters changed)
```

**Visualization:**
- Superpixel segmentation overlay
- Green segments = support predicted class
- Red segments = oppose predicted class
- Intensity = contribution strength

**Measurement:**
- Top positive contributors (segments that support prediction)
- Top negative contributors (segments that oppose)
- Explanation fidelity (how well simplified model matches full model)

---

## Section 6: Misclassification Analysis

**Why:** Learn from mistakes. Identify common failure modes and edge cases.

**Input:** Misclassified test samples
**Process:** Analyze patterns in errors
**Output:** Gallery of mistakes with analysis

```
[st.header] Misclassified Samples Analysis

[st.slider] "Number of samples to show" - 5-50, default 10

For each misclassified sample:
    [st.expander f"Sample {id}: True={X}, Pred={Y} (conf={Z}%)"]
        [st.columns 3]
            col1: [st.image] Sample
            col2: [st.image] Grad-CAM
            col3:
                [st.dataframe] Prediction confidences
                [st.text] Possible reason for misclassification

[st.selectbox] "Filter by": [All, Specific True Class, Specific Pred Class]
```

**Visualization:**
- Gallery of mistakes
- Side-by-side: image, Grad-CAM, confidence scores
- Grouped by error type

**Measurement:**
- Total misclassifications: {count} / {total_test_samples}
- Most common error: {ClassA} → {ClassB} ({count} times)
- Error patterns:
  - Low confidence errors (model uncertain)
  - High confidence errors (model confidently wrong)
  - Systematic errors (consistent confusion between classes)

**Possible Reasons Analysis:**
- "Low confidence (< 50%) - model uncertain"
- "Similar to {other_class} - expected confusion"
- "Poor image quality - may be corrupted"
- "Outlier in feature space - unusual sample"

---

## Section 7: Model Architecture Review

**Why:** Quick reference to model structure. Verify architecture matches expectations.

**Input:** Trained model
**Process:** Extract layer info
**Output:** Architecture table and metrics

```
[st.header] Architecture Summary

[st.expander "Full Model Architecture"]
    [st.text] Layer-by-layer breakdown
    [st.dataframe] Layer table
        Layer | Type | Output Shape | Params | Trainable

[st.columns 3]
    col1: [st.metric] "Total Params" - 2,456,789
    col2: [st.metric] "Model Size" - 38 MB
    col3: [st.metric] "Inference Time" - 12ms per sample

[st.download_button] "Export Architecture Diagram"
```

**Visualization:**
- Layer-by-layer table (scrollable)
- Parameter distribution pie chart (conv vs dense vs other)

**Measurement:**
- Total parameters
- Trainable vs frozen (if transfer learning)
- Model file size
- Inference time per sample (on CPU and GPU)
- FLOPs (computational cost)

---

## Interpretability Summary

**Key Questions This Page Answers:**

1. **Where does the model look?** (Grad-CAM)
2. **How does it organize classes?** (t-SNE)
3. **What patterns does it detect?** (Activation maps, filter weights)
4. **Why did it predict this?** (LIME)
5. **When does it fail?** (Misclassification analysis)
6. **What did it learn?** (Architecture review)
