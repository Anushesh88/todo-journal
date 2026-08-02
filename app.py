import streamlit as st
import datetime
import pandas as pd

# Page configuration MUST be called first
st.set_page_config(
    page_title="ToDo Journal - Streamlit & Google Sheets App",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

from styles import apply_styles
from database import DatabaseManager
from daily_goals_module import render_daily_goals_tab
from task_manager_module import render_task_manager_tab
from notes_module import render_notes_tab
from journal_module import render_journal_tab
from analytics_module import render_analytics_tab

# Initialize theme state
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

IS_DARK = st.session_state.theme == "dark"
apply_styles(IS_DARK)

# Initialize Database Manager
if "db" not in st.session_state:
    st.session_state.db = DatabaseManager()

db: DatabaseManager = st.session_state.db

# -------------------------------------------------------------
# App Header & Controls
# -------------------------------------------------------------
h_col1, h_col2, h_col3 = st.columns([4, 2, 1.2])

with h_col1:
    db_mode_badge = '<span class="badge badge-green">🟢 Google Sheets Sync</span>' if db.mode == "gsheets" else '<span class="badge badge-amber">💾 Local Storage Mode</span>'
    st.markdown(f"""
    <div class="brand-title">
        🎯 To-Do Journal {db_mode_badge}
    </div>
    <div class="brand-subtitle">
        Daily Recurring Goals • Score Calculation • Short & Long-Term Tasks • Google Calendar Sync
    </div>
    """, unsafe_allow_html=True)

with h_col2:
    selected_date = st.date_input(
        "📅 Active Date",
        value=datetime.date.today(),
        help="Select date to manage daily goals, tasks, and journal entries"
    )
    active_date_str = selected_date.strftime("%Y-%m-%d")

with h_col3:
    st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
    theme_btn_text = "☀️ Light Theme" if IS_DARK else "🌙 Dark Theme"
    st.button(theme_btn_text, on_click=toggle_theme, use_container_width=True)

# -------------------------------------------------------------
# Google Sheets Setup Expander (Helpful for deployment)
# -------------------------------------------------------------
with st.expander("ℹ️ Google Sheets & Deployment Configuration Guide"):
    st.markdown("""
    ### How to Connect your Google Sheet:
    1. Create a Google Sheet named **`ToDo_Journal_DB`** on Google Drive.
    2. Create a Google Cloud Service Account & download the JSON Key file.
    3. Share your Google Sheet with the Service Account email (Editor permissions).
    4. Paste the Service Account credentials into `.streamlit/secrets.toml` or Streamlit Community Cloud Secrets:
    ```toml
    [gcp_service_account]
    type = "service_account"
    project_id = "your-project-id"
    private_key_id = "your-private-key-id"
    private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
    client_email = "your-service-account@your-project.iam.gserviceaccount.com"
    client_id = "..."
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    ```
    *Note: If no secrets are provided, the app seamlessly uses local storage (`local_data.json`).*
    """)

# -------------------------------------------------------------
# Main Navigation Tabs
# -------------------------------------------------------------
tab_goals, tab_tasks, tab_notes, tab_journal, tab_analytics = st.tabs([
    "🎯 Daily Goals & Score",
    "📌 Task Manager",
    "📝 Notes & Ideas",
    "📖 Daily Journal",
    "📊 Analytics & Insights"
])

with tab_goals:
    render_daily_goals_tab(db, active_date_str)

with tab_tasks:
    render_task_manager_tab(db, active_date_str)

with tab_notes:
    render_notes_tab(db)

with tab_journal:
    render_journal_tab(db, active_date_str)

with tab_analytics:
    render_analytics_tab(db, IS_DARK)
