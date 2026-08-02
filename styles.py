import streamlit as st

def get_css(is_dark: bool) -> str:
    """Returns custom CSS based on theme selection (dark/light)."""
    bg = "#09090b" if is_dark else "#ffffff"
    bg_subtle = "#121217" if is_dark else "#f8fafc"
    card_bg = "#121217" if is_dark else "#ffffff"
    card_hover = "#181820" if is_dark else "#f1f5f9"
    border = "#27272a" if is_dark else "#e2e8f0"
    border_subtle = "#1f1f23" if is_dark else "#f1f5f9"
    text = "#fafafa" if is_dark else "#0f172a"
    text_muted = "#a1a1aa" if is_dark else "#64748b"
    text_dim = "#71717a" if is_dark else "#94a3b8"
    accent = "#3b82f6"
    accent_bg = "rgba(59, 130, 246, 0.12)"
    green = "#22c55e"
    green_bg = "rgba(34, 197, 94, 0.12)"
    amber = "#f59e0b"
    amber_bg = "rgba(245, 158, 11, 0.12)"
    red = "#ef4444"
    red_bg = "rgba(239, 68, 68, 0.12)"
    purple = "#a855f7"
    purple_bg = "rgba(168, 85, 247, 0.12)"

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300..800;1,9..40,300..800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Hide standard header & footer */
    header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
    div[data-testid="stSidebarCollapsedControl"] {{
        display: none !important;
    }}

    /* Global layout & typography */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"] {{
        background-color: {bg} !important;
        color: {text} !important;
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    .block-container {{
        padding: 1.5rem 2rem 3rem !important;
        max-width: 1280px !important;
    }}

    /* Header & Brand bar */
    .app-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 1.2rem;
        border-bottom: 1px solid {border};
        margin-bottom: 1.5rem;
    }}

    .brand-title {{
        font-size: 1.6rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }}

    .brand-subtitle {{
        font-size: 0.85rem;
        color: {text_muted};
        margin-top: 0.1rem;
    }}

    /* Tab bar styling (Pill style) */
    button[data-baseweb="tab"] {{
        background: transparent !important;
        color: {text_muted} !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        padding: 0.55rem 1.2rem !important;
        border: 1px solid transparent !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }}

    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {text} !important;
        background: {card_bg} !important;
        border-color: {border} !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }}

    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{
        display: none !important;
    }}

    [data-baseweb="tab-list"] {{
        gap: 6px !important;
        background: {bg_subtle} !important;
        border: 1px solid {border} !important;
        border-radius: 12px !important;
        padding: 4px !important;
        margin-bottom: 1.5rem !important;
    }}

    /* Custom Metric / KPI Cards */
    .metric-card {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 1.25rem 1.4rem;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }}

    .metric-card:hover {{
        border-color: {accent};
    }}

    .metric-label {{
        font-size: 0.78rem;
        color: {text_muted};
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    .metric-value {{
        font-size: 1.85rem;
        font-weight: 800;
        color: {text};
        letter-spacing: -0.03em;
        margin-top: 0.2rem;
    }}

    .metric-subtext {{
        font-size: 0.75rem;
        color: {text_dim};
        margin-top: 0.3rem;
    }}

    /* Task & Goal Cards */
    .item-card {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
        transition: all 0.15s ease;
    }}

    .item-card:hover {{
        background: {card_hover};
        border-color: {border};
    }}

    .item-card.completed {{
        opacity: 0.65;
        background: {bg_subtle};
    }}

    /* Badges */
    .badge {{
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        line-height: 1.2;
    }}

    .badge-blue {{ color: {accent}; background: {accent_bg}; }}
    .badge-green {{ color: {green}; background: {green_bg}; }}
    .badge-amber {{ color: {amber}; background: {amber_bg}; }}
    .badge-red {{ color: {red}; background: {red_bg}; }}
    .badge-purple {{ color: {purple}; background: {purple_bg}; }}

    /* Progress bar override */
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, #3b82f6 0%, #22c55e 100%) !important;
        border-radius: 6px !important;
    }}

    /* Chart Wrap */
    .chart-container {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 1.25rem 1.25rem 0.5rem;
        margin-top: 1rem;
    }}

    .chart-title {{
        font-size: 0.95rem;
        font-weight: 700;
        color: {text};
    }}

    .chart-subtitle {{
        font-size: 0.75rem;
        color: {text_muted};
        margin-bottom: 1rem;
    }}

    /* Banner Alerts */
    .rollover-banner {{
        background: {amber_bg};
        border: 1px solid {amber};
        color: {amber};
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 0.85rem;
        font-weight: 500;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    /* Form & Input tweaks */
    div[data-baseweb="input"] input, div[data-baseweb="select"] {{
        border-radius: 8px !important;
    }}

    .stButton button {{
        border-radius: 8px !important;
        font-weight: 600 !important;
    }}

    </style>
    """

def apply_styles(is_dark: bool):
    st.markdown(get_css(is_dark), unsafe_allow_html=True)
