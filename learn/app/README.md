# Malware Classification Streamlit App

Professional multi-page ML dashboard for malware image classification with PyTorch.

---

## 📁 Project Structure

### **Self-Contained Architecture:**

```
app/
├── main.py                      # Entry point + navigation
│
├── content/                     # Self-contained page modules
│   ├── home/
│   │   ├── page.py             # Entry point
│   │   └── view.py             # Home page logic
│   │
│   ├── dataset/                # Dataset configuration
│   │   ├── page.py             # Entry point
│   │   ├── view.py             # Main coordinator with tabs
│   │   └── tab_*.py            # Individual tab implementations
│   │
│   ├── model/                  # Model builder
│   ├── training/               # Training configuration
│   ├── monitor/                # Training monitor
│   ├── results/                # Results & evaluation
│   └── interpret/              # Model interpretability
│
├── components/                  # Shared UI components (flat structure)
│   ├── header.py               # App header with session info
│   ├── sidebar.py              # Configuration status sidebar
│   ├── theme.py                # Theme customization
│   ├── styling.py              # CSS injection
│   └── utils.py                # GPU detection, session management
│
├── state/                       # Session state management (NO __init__.py)
│   ├── workflow.py             # ML workflow state (configs, training)
│   ├── ui.py                   # UI preferences (theme, past sessions)
│   └── cache.py                # Cached data (dataset scans, splits)
│
├── utils/                       # Utility functions
│   ├── dataset_utils.py        # Dataset scanning & processing
│   └── dataset_viz.py          # Dataset visualizations
│
└── .streamlit/
    └── config.toml             # Theme & server config
```

### **Architecture Principles:**

1. **Self-Contained Pages**: Each page in `content/` is fully self-contained in its own folder
2. **Tab-Based Organization**: Complex pages split content into multiple tab files for better organization
3. **No __init__.py**: All imports use absolute paths (e.g., `from content.dataset.view import render`)
4. **Flat Components**: Shared components stay in a flat structure, not nested
5. **State Abstraction**: All session state access goes through `state/` module functions (no direct `st.session_state` access)

---

## 📄 Page Organization

Pages use **tab-based file organization** for complex multi-section content:

### Example: Dataset Page

```
content/dataset/
├── page.py                  # Entry point (calls render_header/sidebar + view.render())
├── view.py                  # Main coordinator (creates st.tabs, calls tab renderers)
├── tab_selection.py         # Tab 1: Dataset selection & train/val/test split
├── tab_preprocessing.py     # Tab 2: Image preprocessing config & preview
├── tab_augmentation.py      # Tab 3: Data augmentation settings
└── tab_samples.py           # Tab 4: Sample image viewer
```

**Each tab file** contains a `render()` function that displays that tab's content.
**The view.py** creates the tabs and delegates to the appropriate tab renderer.

Simpler pages (like Home or Monitor) can use a single `view.py` file.

---

## 🎨 Theme Customization

**Location**: Sidebar → Theme Settings (expandable)

### Color Pickers
- **Primary** - Buttons, links, accents
- **Secondary** - Headers, highlights
- **Background** - Dark mode background

### Presets
- **Soft Green** (default) - `#98c127` / `#bdd373`
- **Soft Blue** - `#8fd7d7` / `#00b0be`
- **Soft Pink** - `#f45f74` / `#ff8ca1`
- **Soft Orange** - `#ffb255` / `#ffcd8e`

Theme colors persist across sessions and apply dynamically via CSS injection.

---

## 🗂️ Navigation Structure

```
Main
  🏠 Home & Session

Workflow
  📊 Dataset Configuration
  🧠 Model Builder
  ⚙️  Training Configuration
  📈 Monitor Training
  🎯 Results & Evaluation
  🔍 Interpretability
```

**Sidebar shows configuration status:**
- ✅ Dataset configured
- ✅ Model configured
- ✅ Training configured

Status indicators update automatically based on session state.

---

## 🚀 Running the App

```bash
cd app
streamlit run main.py
```

The app will open in your browser at `http://localhost:8501`

### Pages & URLs
- `/home` - Home & Session Setup
- `/dataset` - Dataset Configuration (4 tabs)
- `/model` - Model Builder
- `/training` - Training Configuration
- `/monitor` - Training Monitor (live updates)
- `/results` - Results & Evaluation
- `/interpretability` - Model Interpretability

---

## ✅ Current Features

### ✓ Core Infrastructure
- Self-contained page architecture
- Tab-based content organization
- State management abstraction (workflow/UI/cache)
- Theme customization with presets
- GPU detection & memory monitoring
- Session management & persistence

### ✓ Dataset Module
- Automated dataset scanning from `repo/malware`
- Train/validation/test split configuration
- Class distribution visualization
- Sample image preview
- Preprocessing preview (resize, normalization)
- Augmentation presets

### 🔄 In Progress
- Model architecture builder (PyTorch)
- Training pipeline with live monitoring
- Results visualization (metrics, confusion matrix, ROC)
- Interpretability tools (Grad-CAM, t-SNE)

---

## 💻 Development Guidelines

### Adding New Pages
1. Create folder in `content/` with `page.py` and `view.py`
2. For complex pages, add `tab_*.py` files for each tab
3. Import tab renderers in `view.py` and orchestrate with `st.tabs()`
4. Add page to `main.py` navigation

### State Management
- **Never** access `st.session_state` directly
- **Always** use functions from `state/workflow.py`, `state/ui.py`, or `state/cache.py`
- Add new state fields to appropriate module with TypedDict definitions

### Components
- Shared components go in flat `components/` directory
- Page-specific logic stays within that page's `content/` folder
- Use absolute imports: `from components.header import render_header`

---

## 🔍 Key Files

- `main.py` - Entry point, navigation setup, state initialization
- `components/sidebar.py` - Configuration status display
- `state/workflow.py` - ML workflow state (session, configs, training)
- `state/cache.py` - Expensive operation caching (dataset scans)
- `utils/dataset_utils.py` - Dataset scanning & processing logic
