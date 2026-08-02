# 🎯 To-Do Journal App (Streamlit & Google Sheets)

A feature-packed, aesthetic To-Do & Journaling Web Application built using **Streamlit** and backed by **Google Sheets** for cloud data persistence.

---

## 🌟 Key Features

1. **Daily Recurring Goals & Daily Score Engine**:
   - Set daily habits and goals that recur automatically every single day.
   - Check off completion for any active date.
   - Real-time **Daily Score %** calculation (`Completed / Total * 100`) and motivational ratings.

2. **Short-Term & Long-Term Tasks with Mini-Tasks**:
   - Separate tasks into **Short-Term** or **Long-Term** goals.
   - For **Long-Term tasks**, add customizable **Mini-Tasks (Subtasks)** with progress tracking.
   - Set target execution dates and final deadlines.

3. **Automatic Task Rollover**:
   - If a task is scheduled for today (or past days) and is not completed, it automatically rolls forward to the current day upon page launch/date shift!

4. **Optional Google Calendar Integration**:
   - Toggle `"Link to Google Calendar"` per task.
   - 1-Click direct Google Calendar event web links.
   - Download `.ICS` calendar files for Apple Calendar, Outlook, or Google Calendar.

5. **Daily Journal & Reflection**:
   - Track daily mood (😊 Happy, 🚀 Productive, 🧘 Calm, etc.).
   - Log daily highlights, key wins, and gratitude.

6. **Dual Persistence Mode**:
   - **Google Sheets Cloud Database**: Connects via `gspread` service account.
   - **Local Storage Mode**: Automatic fallback to local JSON database if Google Sheets credentials are not configured yet.

7. **Plotly Analytics**:
   - 14-day daily score trend line chart.
   - Task completion status donut charts and short vs long-term distribution.

---

## 🚀 Quick Start (Running Locally)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit App
streamlit run app.py
```

---

## ☁️ Streamlit Community Cloud Hosting & Google Sheets Setup

1. Push your code to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and deploy your repository with `app.py` as the main script.
3. In Streamlit Cloud **App Settings -> Secrets**, add your Google Service Account credentials:

```toml
[google_sheets]
sheet_name = "ToDo_Journal_DB"

[gcp_service_account]
type = "service_account"
project_id = "your-gcp-project-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
...
```

4. Share your Google Sheet named `ToDo_Journal_DB` with the service account email (Editor role).
