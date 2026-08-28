"""
Main Entry Point - Streamlit Multipage App
Defines navigation for self-contained content modules
"""

from state.cache import init_cache_state
from state.ui import init_ui_state
from state.workflow import init_workflow_state
import streamlit as st

# Configure app
st.set_page_config(
    page_title="Malware Classification",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://www.google.com",
        "Report a Bug": "https://www.google.com",
        "About": "https://www.google.com",
    }
)

# Initialize session state
init_workflow_state()
init_ui_state()
init_cache_state()

# Define pages
pages = {
    "Main": [
        st.Page("content/home/page.py", title="Home", icon="🏠", url_path="home"),
    ],
    "Workflow": [
        st.Page("content/dataset/page.py", title="Dataset", icon="📊", url_path="dataset"),
        st.Page("content/model/page.py", title="Model", icon="🧠", url_path="model"),
        st.Page("content/training/page.py", title="Training", icon="⚙️", url_path="training"),
        st.Page("content/monitor/page.py", title="Monitor", icon="📈", url_path="monitor"),
        st.Page("content/results/page.py", title="Results", icon="🎯", url_path="results"),
        st.Page("content/interpret/page.py", title="Interpretability", icon="🔍", url_path="interpretability"),
    ]
}

# Set up navigation
pg = st.navigation(pages)
pg.run()
