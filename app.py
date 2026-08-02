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
    if db.mode == "supabase":
        db_mode_badge = '<span class="badge badge-green">⚡ Supabase Cloud DB</span>'
    elif db.mode == "gsheets":
        db_mode_badge = '<span class="badge badge-green">🟢 Google Sheets Sync</span>'
    else:
        db_mode_badge = '<span class="badge badge-amber">💾 Local Storage Mode</span>'

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
    b_sync, b_theme = st.columns([1, 1])
    with b_sync:
        if st.button("🔄 Sync", help="Force sync and fetch fresh data from Database", use_container_width=True):
            st.session_state.db = DatabaseManager()
            if hasattr(st.session_state.db, "reconnect_and_sync"):
                st.session_state.db.reconnect_and_sync()
            st.rerun()
    with b_theme:
        theme_btn_text = "☀️ Light" if IS_DARK else "🌙 Dark"
        st.button(theme_btn_text, on_click=toggle_theme, use_container_width=True)

# -------------------------------------------------------------
# Database Setup & Configuration Guide
# -------------------------------------------------------------
with st.expander("ℹ️ Database & Deployment Configuration Guide (Supabase / Google Sheets)"):
    st.markdown("""
    ### ⚡ Option 1: Supabase Setup (Recommended - 100% Free & Fast):
    1. Sign up for a free account at [supabase.com](https://supabase.com) and create a project.
    2. Go to **SQL Editor**, click **New Query**, paste the schema below, and click **Run**:
    ```sql
    CREATE TABLE IF NOT EXISTS daily_goals (id TEXT PRIMARY KEY, title TEXT, category TEXT, created_at TEXT, active BOOLEAN DEFAULT TRUE);
    CREATE TABLE IF NOT EXISTS daily_log (id TEXT PRIMARY KEY, date TEXT, goal_id TEXT, completed BOOLEAN DEFAULT FALSE, updated_at TEXT);
    CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, title TEXT, type TEXT, category TEXT, priority TEXT, status TEXT, target_date TEXT, deadline TEXT, created_at TEXT, completed_at TEXT, is_longterm BOOLEAN DEFAULT FALSE, calendar_synced BOOLEAN DEFAULT FALSE);
    CREATE TABLE IF NOT EXISTS subtasks (id TEXT PRIMARY KEY, task_id TEXT, title TEXT, completed BOOLEAN DEFAULT FALSE, created_at TEXT);
    CREATE TABLE IF NOT EXISTS notes (id TEXT PRIMARY KEY, title TEXT, category TEXT, content TEXT, tags TEXT, is_pinned BOOLEAN DEFAULT FALSE, color TEXT, created_at TEXT, updated_at TEXT);
    CREATE TABLE IF NOT EXISTS journal_entries (id TEXT PRIMARY KEY, date TEXT, mood TEXT, main_text TEXT, wins TEXT, gratitude TEXT, score_pct REAL DEFAULT 0.0, created_at TEXT);
    ```
    3. Go to **Project Settings** ➔ **API** in Supabase, and copy your **URL** and `anon` **Key**.
    4. Paste into `.streamlit/secrets.toml` or Streamlit Cloud Secrets:
    ```toml
    [supabase]
    url = "https://your-project-ref.supabase.co"
    key = "your-anon-public-key"
    ```

    ---

    ### 🟢 Option 2: Google Sheets Setup:
    Paste your GCP Service Account JSON into `.streamlit/secrets.toml`:
    ```toml
    [gcp_service_account]
    type = "service_account"
    ...
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
