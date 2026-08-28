def GET_CSS(primary: str, secondary: str, background: str) -> str:
    return f"""
    <style>
    /* Main background */
    .stApp {{
        background-color: {background};
    }}

    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background-color: {background};
    }}

    /* Headers */
    h1, h2, h3 {{
        color: {primary} !important;
    }}

    /* Buttons */
    .stButton>button {{
        background-color: {primary};
        color: {background};
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }}

    .stButton>button:hover {{
        background-color: {secondary};
        border-color: {secondary};
    }}

    /* Primary buttons */
    .stButton>button[kind="primary"] {{
        background-color: {secondary};
    }}

    .stButton>button[kind="primary"]:hover {{
        background-color: {primary};
    }}

    /* Links */
    a {{
        color: {primary} !important;
    }}

    /* Metrics */
    [data-testid="stMetricValue"] {{
        color: {primary};
    }}

    /* Selectbox */
    [data-baseweb="select"] {{
        border-color: {secondary} !important;
    }}

    [data-baseweb="select"]:hover {{
        border-color: {primary} !important;
    }}

    /* Selected option in dropdown */
    [data-baseweb="select"] [data-baseweb="tag"] {{
        background-color: {secondary} !important;
    }}

    /* Slider */
    .stSlider [data-baseweb="slider"] [role="slider"] {{
        background-color: {primary} !important;
    }}

    .stSlider [data-baseweb="slider"] [data-testid="stTickBar"] {{
        background-color: {secondary} !important;
    }}

    /* Radio buttons */
    .stRadio [role="radiogroup"] label {{
        color: #fafafa;
    }}

    .stRadio [role="radio"][aria-checked="true"] {{
        background-color: {primary} !important;
    }}

    .stRadio [role="radio"]:hover {{
        background-color: {secondary} !important;
    }}

    /* Checkboxes */
    .stCheckbox [data-baseweb="checkbox"] {{
        border-color: {secondary} !important;
    }}

    .stCheckbox [data-baseweb="checkbox"][data-checked="true"] {{
        background-color: {primary} !important;
        border-color: {primary} !important;
    }}

    /* Number input */
    .stNumberInput [data-baseweb="input"] {{
        border-color: {secondary} !important;
    }}

    .stNumberInput [data-baseweb="input"]:focus {{
        border-color: {primary} !important;
        box-shadow: 0 0 0 1px {primary} !important;
    }}

    /* Text input */
    .stTextInput input {{
        border-color: {secondary} !important;
    }}

    .stTextInput input:focus {{
        border-color: {primary} !important;
        box-shadow: 0 0 0 1px {primary} !important;
    }}

    /* Color picker */
    .stColorPicker [data-baseweb="input"] {{
        border-color: {secondary} !important;
    }}

    /* Success/info/warning/error boxes */
    .stSuccess {{
        background-color: rgba(152, 193, 39, 0.1);
        border-left: 4px solid {primary};
    }}

    .stInfo {{
        background-color: rgba(143, 215, 215, 0.1);
        border-left: 4px solid {secondary};
    }}

    .stWarning {{
        background-color: rgba(255, 178, 85, 0.1);
        border-left: 4px solid #ffb255;
    }}

    .stError {{
        background-color: rgba(244, 95, 116, 0.1);
        border-left: 4px solid #f45f74;
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        border-radius: 4px;
        border: 1px solid {secondary} !important;
    }}

    .streamlit-expanderHeader:hover {{
        border-color: {primary} !important;
        background-color: rgba(152, 193, 39, 0.05);
    }}

    /* Navigation links spacing */
    [data-testid="stSidebarNav"] a {{
        padding: 0.5rem 1rem;
        margin: 0.2rem 0;
        border-radius: 4px;
    }}

    [data-testid="stSidebarNav"] a:hover {{
        background-color: rgba(152, 193, 39, 0.1);
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab"] {{
        color: {secondary};
    }}

    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: {primary};
        border-bottom-color: {primary} !important;
    }}

    /* Divider */
    hr {{
        border-color: {secondary} !important;
    }}

    /* Progress bar */
    .stProgress > div > div {{
        background-color: {primary} !important;
    }}

    /* Spinner */
    .stSpinner > div {{
        border-top-color: {primary} !important;
    }}
    </style>
    """
