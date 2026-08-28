"""
Page: Training Monitor
Self-contained page module
"""

from components.header import render_header
from components.sidebar import render_sidebar
from content.monitor.view import render

render_header()
render_sidebar()

render()
