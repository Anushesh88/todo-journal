import json
import os
import datetime
import pandas as pd
import streamlit as st

# Optional gspread imports
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False


LOCAL_DB_FILE = "local_data.json"

DEFAULT_INITIAL_DATA = {
    "Daily_Goals": [
        {"id": "dg_1", "title": "Morning Meditation & Breathing (10 mins)", "category": "Wellness", "created_at": "2026-08-01", "active": True},
        {"id": "dg_2", "title": "30 Minutes Exercise / Walk", "category": "Health", "created_at": "2026-08-01", "active": True},
        {"id": "dg_3", "title": "Read 15 pages of a book", "category": "Learning", "created_at": "2026-08-01", "active": True},
        {"id": "dg_4", "title": "Review daily priorities & journal", "category": "Productivity", "created_at": "2026-08-01", "active": True}
    ],
    "Daily_Log": [],
    "Tasks": [
        {
            "id": "t_1",
            "title": "Complete project proposal document",
            "type": "Short-Term",
            "category": "Work",
            "priority": "High",
            "status": "Pending",
            "target_date": datetime.date.today().strftime("%Y-%m-%d"),
            "deadline": datetime.date.today().strftime("%Y-%m-%d"),
            "created_at": datetime.date.today().strftime("%Y-%m-%d"),
            "completed_at": "",
            "is_longterm": False,
            "calendar_synced": False
        },
        {
            "id": "t_2",
            "title": "Build Streamlit To-Do & Journal App",
            "type": "Long-Term",
            "category": "Development",
            "priority": "High",
            "status": "In Progress",
            "target_date": datetime.date.today().strftime("%Y-%m-%d"),
            "deadline": (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d"),
            "created_at": datetime.date.today().strftime("%Y-%m-%d"),
            "completed_at": "",
            "is_longterm": True,
            "calendar_synced": False
        }
    ],
    "Subtasks": [
        {"id": "st_1", "task_id": "t_2", "title": "Setup Google Sheets backend architecture", "completed": True, "created_at": datetime.date.today().strftime("%Y-%m-%d")},
        {"id": "st_2", "task_id": "t_2", "title": "Implement Daily Goals score engine & automatic recurrence", "completed": False, "created_at": datetime.date.today().strftime("%Y-%m-%d")},
        {"id": "st_3", "task_id": "t_2", "title": "Build Long-term mini-tasks & Google Calendar sync", "completed": False, "created_at": datetime.date.today().strftime("%Y-%m-%d")}
    ],
    "Journal_Entries": [],
    "Notes": [
        {
            "id": "n_1",
            "title": "💡 App Architecture & Feature Ideas",
            "category": "Ideas",
            "content": "### Key Ideas for Next Release\n- Integrations with Google Tasks & Notion\n- AI Summary for weekly journaling\n- Custom color themes per project tag",
            "tags": "architecture, ideas, features",
            "is_pinned": True,
            "color": "purple",
            "created_at": datetime.date.today().strftime("%Y-%m-%d"),
            "updated_at": datetime.date.today().strftime("%Y-%m-%d")
        },
        {
            "id": "n_2",
            "title": "📚 Daily Reading Quotes & Key Takeaways",
            "category": "Learning",
            "content": "> 'Consistency is what transforms average into excellence.'\n\n- Practice 15 mins daily habit stacking.\n- Track score weekly in Analytics tab.",
            "tags": "quotes, reading, habits",
            "is_pinned": False,
            "color": "blue",
            "created_at": datetime.date.today().strftime("%Y-%m-%d"),
            "updated_at": datetime.date.today().strftime("%Y-%m-%d")
        }
    ]
}


class DatabaseManager:
    def __init__(self):
        self.mode = "local"  # 'gsheets' or 'local'
        self.client = None
        self.spreadsheet = None
        self.local_file = LOCAL_DB_FILE
        self._init_connection()

    def _init_connection(self):
        """Attempts Google Sheets connection via Streamlit secrets, falls back to Local File DB."""
        if GSPREAD_AVAILABLE:
            try:
                if "gcp_service_account" in st.secrets:
                    scopes = [
                        "https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/drive"
                    ]
                    creds_dict = dict(st.secrets["gcp_service_account"])
                    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                    self.client = gspread.authorize(creds)
                    
                    sheet_name = st.secrets.get("google_sheets", {}).get("sheet_name", "ToDo_Journal_DB")
                    sheet_url_or_id = st.secrets.get("google_sheets", {}).get("sheet_url_or_id", "")
                    
                    try:
                        if sheet_url_or_id:
                            if "docs.google.com" in sheet_url_or_id:
                                self.spreadsheet = self.client.open_by_url(sheet_url_or_id)
                            else:
                                self.spreadsheet = self.client.open_by_key(sheet_url_or_id)
                        else:
                            self.spreadsheet = self.client.open(sheet_name)
                    except Exception:
                        try:
                            self.spreadsheet = self.client.create(sheet_name)
                        except Exception as create_err:
                            st.warning(f"Could not create Google Sheet automatically ({create_err}). Please create a Google Sheet named '{sheet_name}' on your Google Drive and share it with '{creds_dict.get('client_email')}' as Editor.")
                            self.mode = "local"
                            self._ensure_local_file()
                            return
                    
                    self.mode = "gsheets"
                    self._ensure_gsheet_tables()
                    return
            except Exception as e:
                pass

        self.mode = "local"
        self._ensure_local_file()

    def _ensure_local_file(self):
        if not os.path.exists(self.local_file):
            with open(self.local_file, "w") as f:
                json.dump(DEFAULT_INITIAL_DATA, f, indent=2)

    def _load_local_data(self) -> dict:
        self._ensure_local_file()
        try:
            with open(self.local_file, "r") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_INITIAL_DATA

    def _save_local_data(self, data: dict):
        with open(self.local_file, "w") as f:
            json.dump(data, f, indent=2)

    def _ensure_gsheet_tables(self):
        """Creates required worksheets if missing in Google Sheets."""
        existing_worksheets = [ws.title for ws in self.spreadsheet.worksheets()]
        for table, items in DEFAULT_INITIAL_DATA.items():
            if table not in existing_worksheets:
                ws = self.spreadsheet.add_worksheet(title=table, rows=100, cols=20)
                if items:
                    headers = list(items[0].keys())
                    ws.append_row(headers)
                    for item in items:
                        ws.append_row([str(item.get(h, "")) for h in headers])

    # -------------------------------------------------------------
    # DAILY GOALS
    # -------------------------------------------------------------
    def get_daily_goals(self) -> list:
        if self.mode == "local":
            data = self._load_local_data()
            return [g for g in data.get("Daily_Goals", []) if g.get("active", True)]
        else:
            try:
                ws = self.spreadsheet.worksheet("Daily_Goals")
                records = ws.get_all_records()
                return [r for r in records if str(r.get("active", "")).lower() in ["true", "1"]]
            except Exception:
                return []

    def add_daily_goal(self, title: str, category: str = "General") -> str:
        goal_id = f"dg_{int(datetime.datetime.now().timestamp())}"
        created_at = datetime.date.today().strftime("%Y-%m-%d")
        new_goal = {
            "id": goal_id,
            "title": title,
            "category": category,
            "created_at": created_at,
            "active": True
        }
        if self.mode == "local":
            data = self._load_local_data()
            data["Daily_Goals"].append(new_goal)
            self._save_local_data(data)
        else:
            ws = self.spreadsheet.worksheet("Daily_Goals")
            ws.append_row([goal_id, title, category, created_at, "True"])
        return goal_id

    def delete_daily_goal(self, goal_id: str):
        if self.mode == "local":
            data = self._load_local_data()
            data["Daily_Goals"] = [g for g in data["Daily_Goals"] if g["id"] != goal_id]
            self._save_local_data(data)
        else:
            ws = self.spreadsheet.worksheet("Daily_Goals")
            records = ws.get_all_records()
            for idx, r in enumerate(records, start=2):
                if str(r.get("id")) == str(goal_id):
                    ws.delete_rows(idx)
                    break

    # -------------------------------------------------------------
    # DAILY LOG & SCORES
    # -------------------------------------------------------------
    def get_daily_log(self, date_str: str) -> dict:
        """Returns map of goal_id -> bool completion status for date."""
        if self.mode == "local":
            data = self._load_local_data()
            logs = [l for l in data.get("Daily_Log", []) if l.get("date") == date_str]
            return {l["goal_id"]: l["completed"] for l in logs}
        else:
            try:
                ws = self.spreadsheet.worksheet("Daily_Log")
                records = ws.get_all_records()
                date_logs = [r for r in records if str(r.get("date")) == date_str]
                return {r["goal_id"]: str(r.get("completed")).lower() in ["true", "1"] for r in date_logs}
            except Exception:
                return {}

    def toggle_daily_goal(self, goal_id: str, date_str: str, completed: bool):
        if self.mode == "local":
            data = self._load_local_data()
            logs = data.get("Daily_Log", [])
            found = False
            for l in logs:
                if l.get("date") == date_str and l.get("goal_id") == goal_id:
                    l["completed"] = completed
                    l["updated_at"] = datetime.datetime.now().isoformat()
                    found = True
                    break
            if not found:
                logs.append({
                    "id": f"log_{int(datetime.datetime.now().timestamp())}",
                    "date": date_str,
                    "goal_id": goal_id,
                    "completed": completed,
                    "updated_at": datetime.datetime.now().isoformat()
                })
            data["Daily_Log"] = logs
            self._save_local_data(data)
        else:
            ws = self.spreadsheet.worksheet("Daily_Log")
            records = ws.get_all_records()
            found_idx = None
            for idx, r in enumerate(records, start=2):
                if str(r.get("date")) == date_str and str(r.get("goal_id")) == goal_id:
                    found_idx = idx
                    break
            if found_idx:
                ws.update_cell(found_idx, 4, str(completed))
            else:
                log_id = f"log_{int(datetime.datetime.now().timestamp())}"
                ws.append_row([log_id, date_str, goal_id, str(completed), datetime.datetime.now().isoformat()])

    def calculate_daily_score(self, date_str: str) -> tuple:
        """Returns (score_percentage, completed_count, total_count)."""
        goals = self.get_daily_goals()
        if not goals:
            return 0.0, 0, 0
        log_map = self.get_daily_log(date_str)
        completed_count = sum(1 for g in goals if log_map.get(g["id"], False))
        total_count = len(goals)
        pct = round((completed_count / total_count) * 100, 1) if total_count > 0 else 0.0
        return pct, completed_count, total_count

    # -------------------------------------------------------------
    # TASKS (SHORT-TERM & LONG-TERM)
    # -------------------------------------------------------------
    def get_tasks(self) -> list:
        if self.mode == "local":
            data = self._load_local_data()
            return data.get("Tasks", [])
        else:
            try:
                ws = self.spreadsheet.worksheet("Tasks")
                return ws.get_all_records()
            except Exception:
                return []

    def add_task(self, title: str, task_type: str, category: str, priority: str, target_date: str, deadline: str, is_longterm: bool) -> str:
        task_id = f"t_{int(datetime.datetime.now().timestamp())}"
        created_at = datetime.date.today().strftime("%Y-%m-%d")
        new_task = {
            "id": task_id,
            "title": title,
            "type": task_type,
            "category": category,
            "priority": priority,
            "status": "Pending",
            "target_date": target_date,
            "deadline": deadline,
            "created_at": created_at,
            "completed_at": "",
            "is_longterm": is_longterm,
            "calendar_synced": False
        }
        if self.mode == "local":
            data = self._load_local_data()
            data["Tasks"].append(new_task)
            self._save_local_data(data)
        else:
            ws = self.spreadsheet.worksheet("Tasks")
            ws.append_row(list(new_task.values()))
        return task_id

    def update_task_status(self, task_id: str, status: str):
        completed_at = datetime.date.today().strftime("%Y-%m-%d") if status == "Completed" else ""
        if self.mode == "local":
            data = self._load_local_data()
            for t in data.get("Tasks", []):
                if t["id"] == task_id:
                    t["status"] = status
                    t["completed_at"] = completed_at
                    break
            self._save_local_data(data)
        else:
            ws = self.spreadsheet.worksheet("Tasks")
            records = ws.get_all_records()
            for idx, r in enumerate(records, start=2):
                if str(r.get("id")) == str(task_id):
                    ws.update_cell(idx, 6, status)  # status column
                    ws.update_cell(idx, 10, completed_at)
                    break

    def delete_task(self, task_id: str):
        if self.mode == "local":
            data = self._load_local_data()
            data["Tasks"] = [t for t in data.get("Tasks", []) if t["id"] != task_id]
            data["Subtasks"] = [st for st in data.get("Subtasks", []) if st["task_id"] != task_id]
            self._save_local_data(data)
        else:
            ws = self.spreadsheet.worksheet("Tasks")
            records = ws.get_all_records()
            for idx, r in enumerate(records, start=2):
                if str(r.get("id")) == str(task_id):
                    ws.delete_rows(idx)
                    break

    # -------------------------------------------------------------
    # AUTOMATIC TASK ROLLOVER ENGINE
    # -------------------------------------------------------------
    def perform_task_rollover(self, today_str: str) -> int:
        """Finds non-completed tasks scheduled BEFORE today and rolls their target date to today."""
        rolled_over_count = 0
        if self.mode == "local":
            data = self._load_local_data()
            tasks = data.get("Tasks", [])
            for t in tasks:
                if t.get("status") != "Completed" and t.get("target_date") and t.get("target_date") < today_str:
                    t["target_date"] = today_str
                    rolled_over_count += 1
            if rolled_over_count > 0:
                self._save_local_data(data)
        else:
            try:
                ws = self.spreadsheet.worksheet("Tasks")
                records = ws.get_all_records()
                for idx, r in enumerate(records, start=2):
                    status = str(r.get("status", ""))
                    target_date = str(r.get("target_date", ""))
                    if status != "Completed" and target_date and target_date < today_str:
                        ws.update_cell(idx, 7, today_str)  # target_date column
                        rolled_over_count += 1
            except Exception:
                pass
        return rolled_over_count

    # -------------------------------------------------------------
    # SUBTASKS / MINI-TASKS
    # -------------------------------------------------------------
    def get_subtasks(self, task_id: str) -> list:
        if self.mode == "local":
            data = self._load_local_data()
            return [st for st in data.get("Subtasks", []) if st.get("task_id") == task_id]
        else:
            try:
                ws = self.spreadsheet.worksheet("Subtasks")
                records = ws.get_all_records()
                return [r for r in records if str(r.get("task_id")) == str(task_id)]
            except Exception:
                return []

    def add_subtask(self, task_id: str, title: str) -> str:
        st_id = f"st_{int(datetime.datetime.now().timestamp())}"
        new_st = {
            "id": st_id,
            "task_id": task_id,
            "title": title,
            "completed": False,
            "created_at": datetime.date.today().strftime("%Y-%m-%d")
        }
        if self.mode == "local":
            data = self._load_local_data()
            data["Subtasks"].append(new_st)
            self._save_local_data(data)
        else:
            ws = self.spreadsheet.worksheet("Subtasks")
            ws.append_row([st_id, task_id, title, "False", datetime.date.today().strftime("%Y-%m-%d")])
        return st_id

    def toggle_subtask(self, subtask_id: str, completed: bool):
        if self.mode == "local":
            data = self._load_local_data()
            for st in data.get("Subtasks", []):
                if st["id"] == subtask_id:
                    st["completed"] = completed
                    break
            self._save_local_data(data)
        else:
            ws = self.spreadsheet.worksheet("Subtasks")
            records = ws.get_all_records()
            for idx, r in enumerate(records, start=2):
                if str(r.get("id")) == str(subtask_id):
                    ws.update_cell(idx, 4, str(completed))
                    break

    def delete_subtask(self, subtask_id: str):
        if self.mode == "local":
            data = self._load_local_data()
            data["Subtasks"] = [st for st in data.get("Subtasks", []) if st["id"] != subtask_id]
            self._save_local_data(data)
        else:
            ws = self.spreadsheet.worksheet("Subtasks")
            records = ws.get_all_records()
            for idx, r in enumerate(records, start=2):
                if str(r.get("id")) == str(subtask_id):
                    ws.delete_rows(idx)
                    break

    # -------------------------------------------------------------
    # JOURNAL ENTRIES
    # -------------------------------------------------------------
    def get_journal_entry(self, date_str: str) -> dict:
        if self.mode == "local":
            data = self._load_local_data()
            entries = [e for e in data.get("Journal_Entries", []) if e.get("date") == date_str]
            return entries[0] if entries else {}
        else:
            try:
                ws = self.spreadsheet.worksheet("Journal_Entries")
                records = ws.get_all_records()
                entries = [r for r in records if str(r.get("date")) == date_str]
                return entries[0] if entries else {}
            except Exception:
                return {}

    def save_journal_entry(self, date_str: str, mood: str, main_text: str, wins: str, gratitude: str, score_pct: float):
        entry_id = f"j_{date_str}"
        entry_data = {
            "id": entry_id,
            "date": date_str,
            "mood": mood,
            "main_text": main_text,
            "wins": wins,
            "gratitude": gratitude,
            "score_pct": score_pct,
            "created_at": datetime.datetime.now().isoformat()
        }
        if self.mode == "local":
            data = self._load_local_data()
            entries = data.get("Journal_Entries", [])
            found = False
            for idx, e in enumerate(entries):
                if e.get("date") == date_str:
                    entries[idx] = entry_data
                    found = True
                    break
            if not found:
                entries.append(entry_data)
            data["Journal_Entries"] = entries
            self._save_local_data(data)
        else:
            ws = self.spreadsheet.worksheet("Journal_Entries")
            records = ws.get_all_records()
            found_idx = None
            for idx, r in enumerate(records, start=2):
                if str(r.get("date")) == date_str:
                    found_idx = idx
                    break
            row_vals = [entry_id, date_str, mood, main_text, wins, gratitude, score_pct, datetime.datetime.now().isoformat()]
            if found_idx:
                for c_idx, val in enumerate(row_vals, start=1):
                    ws.update_cell(found_idx, c_idx, str(val))
            else:
                ws.append_row([str(v) for v in row_vals])

    # -------------------------------------------------------------
    # NOTES ENGINE
    # -------------------------------------------------------------
    def get_notes(self) -> list:
        if self.mode == "local":
            data = self._load_local_data()
            return data.get("Notes", [])
        else:
            try:
                ws = self.spreadsheet.worksheet("Notes")
                return ws.get_all_records()
            except Exception:
                return []

    def add_note(self, title: str, category: str, content: str, tags: str = "", is_pinned: bool = False, color: str = "blue") -> str:
        note_id = f"n_{int(datetime.datetime.now().timestamp())}"
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        new_note = {
            "id": note_id,
            "title": title,
            "category": category,
            "content": content,
            "tags": tags,
            "is_pinned": is_pinned,
            "color": color,
            "created_at": today_str,
            "updated_at": today_str
        }
        if self.mode == "local":
            data = self._load_local_data()
            if "Notes" not in data:
                data["Notes"] = []
            data["Notes"].append(new_note)
            self._save_local_data(data)
        else:
            ws = self.spreadsheet.worksheet("Notes")
            ws.append_row(list(new_note.values()))
        return note_id

    def update_note(self, note_id: str, title: str, category: str, content: str, tags: str = "", is_pinned: bool = False, color: str = "blue"):
        updated_at = datetime.date.today().strftime("%Y-%m-%d")
        if self.mode == "local":
            data = self._load_local_data()
            for n in data.get("Notes", []):
                if n["id"] == note_id:
                    n["title"] = title
                    n["category"] = category
                    n["content"] = content
                    n["tags"] = tags
                    n["is_pinned"] = is_pinned
                    n["color"] = color
                    n["updated_at"] = updated_at
                    break
            self._save_local_data(data)
        else:
            ws = self.spreadsheet.worksheet("Notes")
            records = ws.get_all_records()
            for idx, r in enumerate(records, start=2):
                if str(r.get("id")) == str(note_id):
                    ws.update_cell(idx, 2, title)
                    ws.update_cell(idx, 3, category)
                    ws.update_cell(idx, 4, content)
                    ws.update_cell(idx, 5, tags)
                    ws.update_cell(idx, 6, str(is_pinned))
                    ws.update_cell(idx, 7, color)
                    ws.update_cell(idx, 9, updated_at)
                    break

    def toggle_note_pin(self, note_id: str, is_pinned: bool):
        if self.mode == "local":
            data = self._load_local_data()
            for n in data.get("Notes", []):
                if n["id"] == note_id:
                    n["is_pinned"] = is_pinned
                    break
            self._save_local_data(data)
        else:
            ws = self.spreadsheet.worksheet("Notes")
            records = ws.get_all_records()
            for idx, r in enumerate(records, start=2):
                if str(r.get("id")) == str(note_id):
                    ws.update_cell(idx, 6, str(is_pinned))
                    break

    def delete_note(self, note_id: str):
        if self.mode == "local":
            data = self._load_local_data()
            data["Notes"] = [n for n in data.get("Notes", []) if n["id"] != note_id]
            self._save_local_data(data)
        else:
            ws = self.spreadsheet.worksheet("Notes")
            records = ws.get_all_records()
            for idx, r in enumerate(records, start=2):
                if str(r.get("id")) == str(note_id):
                    ws.delete_rows(idx)
                    break

