# Sidebar (Global - All Pages)

## Why This Exists
**Purpose:** Persistent navigation and status information across all pages. Quick access to resources and settings.

---

## Navigation Section

**Why:** Allow jumping between pages without following linear workflow

```
[st.logo] Project logo

[st.divider]

[st.sidebar.header] Navigation
[st.navigation] (automatic page links)
    - Home & Setup
    - Dataset Configuration
    - Model Configuration
    - Training Configuration
    - Training Monitor
    - Results & Evaluation
    - Model Interpretability
```

**Visualization:**
- Current page highlighted (bold + colored background)
- Completed pages have checkmark icon
- Disabled pages (grayed out) if prerequisites not met

---

## Current Session Section

**Why:** Track which experiment/session user is working on

```
[st.divider]

[st.sidebar.header] Current Session
[st.text] Session ID: {id}
[st.text] Status: {status}
```

**Visualization:**
- Session ID as clickable badge (clicking shows full config)
- Status badge with color:
  - Blue: Configuring
  - Yellow: Training
  - Green: Completed
  - Red: Failed

**Measurement:**
- Current session ID from `st.session_state.session_id`
- Status inferred from page state

---

## Resource Monitor Section

**Why:** Real-time system resource visibility

```
[st.divider]

[st.sidebar.header] Quick Info
[st.metric] "GPU" - Available / Not Available
[st.metric] "Memory" - 4.2/8.0 GB
```

**Visualization:**
- GPU status:
  - Green badge "Available" if `torch.cuda.is_available()`
  - Red badge "Not Available" otherwise
- Memory bar:
  - Horizontal progress bar showing GPU memory usage
  - Updates every 5s if training

**Measurement:**
- **GPU status:** `torch.cuda.is_available()`
- **GPU memory:**
  - Used: `torch.cuda.memory_allocated() / 1e9` GB
  - Total: `torch.cuda.get_device_properties(0).total_memory / 1e9` GB
  - Percentage: `(used / total) * 100`
- **CPU memory (if no GPU):**
  - `psutil.virtual_memory().percent`
- **Disk space:**
  - `psutil.disk_usage('/').free / 1e9` GB free

---

## Settings Section

**Why:** App-level settings accessible from anywhere

```
[st.divider]

[st.sidebar.header] Settings
[st.toggle] "Auto-save Progress"
```

**Visualization:**
- Toggle switches for boolean settings
- Settings persist in `st.session_state`

**Measurement:**
- Auto-save enabled: Save config after each page completion
- Auto-save frequency: Every 30 seconds during training

---

## Resources Section

**Why:** Quick access to documentation and help

```
[st.divider]

[st.sidebar.header] Resources
[st.link_button] "Activation Guide" - Links to activation.md
[st.link_button] "Architecture Doc" - Links to arch.md
[st.link_button] "Help"
```

**Visualization:**
- Link buttons open in new tab or expander
- Help button shows tooltips/FAQ

**Measurement:** None

---

## Collapsible Sidebar

**Note:** Streamlit sidebar can be collapsed by user. All info should be accessible from main page if sidebar hidden.

---

## Sidebar Behavior by Page

| Page | Sidebar Special Elements |
|------|-------------------------|
| Home | Show recent sessions list |
| Dataset | Show selected datasets badge |
| Model | Show parameter count estimate |
| Training | Show current epoch/progress mini-bar |
| Monitor | Show real-time GPU usage graph |
| Results | Show accuracy badge |
| Interpretability | Show selected sample info |
