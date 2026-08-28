"""
Home & Setup Page
Self-contained page module
"""

from components.header import render_header
from components.sidebar import render_sidebar
from content.home.view import render

# Render persistent header and sidebar
render_header()
render_sidebar()

# Render home page content
render()
