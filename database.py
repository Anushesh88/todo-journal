import json
import os
import datetime
import pandas as pd
import streamlit as st

# Optional Supabase import
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# Optional gspread import
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
        {"id": "st_1", "task_id": "t_2", "title": "Setup database backend architecture", "completed": True, "created_at": datetime.date.today().strftime("%Y-%m-%d")},
        {"id": "st_2", "task_id": "t_2", "title": "Implement Daily Goals score engine & automatic recurrence", "completed": False, "created_at": datetime.date.today().strftime("%Y-%m-%d")},
        {"id": "st_3", "task_id": "t_2", "title": "Build Long-term mini-tasks & Google Calendar sync", "completed": False, "created_at": datetime.date.today().strftime("%Y-%m-%d")}
    ],
    "Journal_Entries": [],
    "Notes": [
        {
            "id": "n_1",
            "title": "💡 App Architecture & Feature Ideas",
            "category": "Ideas",
            "content": "### Key Ideas for Next Release\n- Supabase PostgreSQL Cloud DB Integration\n- AI Summary for weekly journaling\n- Custom color themes per project tag",
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
        self.mode = "local"  # 'supabase', 'gsheets', or 'local'
        self.supabase_client = None
        self.client = None
        self.spreadsheet = None
        self.connection_error = None
        self.local_file = LOCAL_DB_FILE
        self._cache = {}
        self._cache_time = {}
        self.cache_ttl = 15  # 15 seconds TTL
        self._init_connection()

    def _init_connection(self):
        """Attempts Supabase connection first, then Google Sheets, then Local File DB."""
        # 1. Try Supabase Connection
        if SUPABASE_AVAILABLE and "supabase" in st.secrets:
            try:
                sup_sec = st.secrets["supabase"]
                url = sup_sec.get("url") or sup_sec.get("SUPABASE_URL")
                key = sup_sec.get("key") or sup_sec.get("SUPABASE_KEY")
                if url and key:
                    self.supabase_client = create_client(url, key)
                    self.mode = "supabase"
                    self.connection_error = None
                    self.sync_unpushed_data()
                    return
            except Exception as e:
                self.connection_error = f"Supabase Error: {e}"

        # 2. Try Google Sheets Connection (Backup)
        if GSPREAD_AVAILABLE and "gcp_service_account" in st.secrets:
            try:
                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
                creds_dict = dict(st.secrets["gcp_service_account"])
                if "private_key" in creds_dict and isinstance(creds_dict["private_key"], str):
                    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

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
                        self.mode = "local"
                        self._ensure_local_file()
                        return
                
                self.mode = "gsheets"
                self.connection_error = None
                self._ensure_gsheet_tables()
                self.sync_unpushed_data()
                return
            except Exception as e:
                self.connection_error = str(e)

        self.mode = "local"
        self._ensure_local_file()

    def reconnect_and_sync(self):
        """Forces re-initializing connection and pulling fresh data from active Database backend."""
        self._cache.clear()
        self._cache_time.clear()
        self._init_connection()
        if self.mode in ["supabase", "gsheets"]:
            self.sync_unpushed_data()
            for table in ["Daily_Goals", "Daily_Log", "Tasks", "Subtasks", "Notes", "Journal_Entries"]:
                self._get_table_records(table, force_refresh=True)

    def sync_unpushed_data(self):
        """Scans local cache and pushes any missing rows to Supabase or Google Sheets."""
        data = self._load_local_data()
        for table_name, items in data.items():
            if not items or not isinstance(items, list):
                continue
            if self.mode == "supabase" and self.supabase_client:
                try:
                    tbl = table_name.lower()
                    res = self.supabase_client.table(tbl).select("id").execute()
                    existing_ids = {str(r.get("id")) for r in (res.data if res and res.data else [])}
                    for item in items:
                        item_id = str(item.get("id", ""))
                        if item_id and item_id not in existing_ids:
                            self.supabase_client.table(tbl).upsert(item).execute()
                            existing_ids.add(item_id)
                except Exception:
                    pass
            elif self.mode == "gsheets" and self.spreadsheet:
                try:
                    ws = self._get_or_create_worksheet(table_name)
                    if ws:
                        records = ws.get_all_records()
                        existing_ids = {str(r.get("id")) for r in records if "id" in r and r.get("id")}
                        for item in items:
                            item_id = str(item.get("id", ""))
                            if item_id and item_id not in existing_ids:
                                row_vals = [str(v) for v in item.values()]
                                ws.append_row(row_vals)
                                existing_ids.add(item_id)
                except Exception:
                    pass

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

    def _get_or_create_worksheet(self, title: str, headers: list = None):
        """Safely gets a worksheet or creates it if missing (Google Sheets)."""
        if not self.spreadsheet:
            return None
        try:
            return self.spreadsheet.worksheet(title)
        except Exception:
            try:
                ws = self.spreadsheet.add_worksheet(title=title, rows=100, cols=20)
                if headers:
                    ws.append_row(headers)
                elif title in DEFAULT_INITIAL_DATA and DEFAULT_INITIAL_DATA[title]:
                    ws.append_row(list(DEFAULT_INITIAL_DATA[title][0].keys()))
                return ws
            except Exception:
                return None

    def _ensure_gsheet_tables(self):
        """Creates required worksheets if missing in Google Sheets."""
        try:
            for table, items in DEFAULT_INITIAL_DATA.items():
                headers = list(items[0].keys()) if items else None
                self._get_or_create_worksheet(table, headers)
        except Exception:
            pass

    def _invalidate_cache(self, table_name: str):
        """Invalidate cache for a specific table after mutation."""
        if table_name in self._cache:
            del self._cache[table_name]
        if table_name in self._cache_time:
            del self._cache_time[table_name]

    def _get_table_records(self, table_name: str, force_refresh: bool = False) -> list:
        """High performance cached record fetcher."""
        now = datetime.datetime.now().timestamp()
        if not force_refresh and table_name in self._cache and (now - self._cache_time.get(table_name, 0)) < self.cache_ttl:
            return self._cache[table_name]

        records = []
        if self.mode == "supabase" and self.supabase_client:
            try:
                tbl = table_name.lower()
                res = self.supabase_client.table(tbl).select("*").execute()
                records = res.data if res and res.data else []
                # Check for unpushed items in local storage
                data = self._load_local_data()
                local_items = data.get(table_name, [])
                existing_ids = {str(r.get("id")) for r in records if "id" in r and r.get("id")}
                unpushed = [item for item in local_items if str(item.get("id")) and str(item.get("id")) not in existing_ids]
                for item in unpushed:
                    try:
                        self.supabase_client.table(tbl).upsert(item).execute()
                        records.append(item)
                    except Exception:
                        pass
                self._cache[table_name] = records
                self._cache_time[table_name] = now
                data[table_name] = records
                self._save_local_data(data)
                return records
            except Exception:
                pass

        elif self.mode == "gsheets":
            try:
                ws = self._get_or_create_worksheet(table_name)
                if ws:
                    records = ws.get_all_records()
                    data = self._load_local_data()
                    local_items = data.get(table_name, [])
                    existing_ids = {str(r.get("id")) for r in records if "id" in r and r.get("id")}
                    unpushed = [item for item in local_items if str(item.get("id")) and str(item.get("id")) not in existing_ids]
                    for item in unpushed:
                        try:
                            ws.append_row([str(v) for v in item.values()])
                            records.append(item)
                        except Exception:
                            pass
                    self._cache[table_name] = records
                    self._cache_time[table_name] = now
                    data[table_name] = records
                    self._save_local_data(data)
                    return records
            except Exception:
                pass

        data = self._load_local_data()
        records = data.get(table_name, [])
        self._cache[table_name] = records
        self._cache_time[table_name] = now
        return records

    def _db_insert(self, table_name: str, item_dict: dict):
        self._invalidate_cache(table_name)
        data = self._load_local_data()
        if table_name not in data:
            data[table_name] = []
        data[table_name].append(item_dict)
        self._save_local_data(data)

        if self.mode == "supabase" and self.supabase_client:
            try:
                self.supabase_client.table(table_name.lower()).upsert(item_dict).execute()
            except Exception:
                pass
        elif self.mode == "gsheets":
            try:
                ws = self._get_or_create_worksheet(table_name)
                if ws:
                    ws.append_row([str(v) for v in item_dict.values()])
            except Exception:
                pass

    def _db_update(self, table_name: str, item_id: str, update_dict: dict):
        self._invalidate_cache(table_name)
        data = self._load_local_data()
        for item in data.get(table_name, []):
            if str(item.get("id")) == str(item_id):
                item.update(update_dict)
                break
        self._save_local_data(data)

        if self.mode == "supabase" and self.supabase_client:
            try:
                self.supabase_client.table(table_name.lower()).update(update_dict).eq("id", item_id).execute()
            except Exception:
                pass
        elif self.mode == "gsheets":
            try:
                ws = self._get_or_create_worksheet(table_name)
                if ws:
                    records = ws.get_all_records()
                    for idx, r in enumerate(records, start=2):
                        if str(r.get("id")) == str(item_id):
                            for key, val in update_dict.items():
                                if key in r:
                                    col_keys = list(r.keys())
                                    if key in col_keys:
                                        c_idx = col_keys.index(key) + 1
                                        ws.update_cell(idx, c_idx, str(val))
                            break
            except Exception:
                pass

    def _db_delete(self, table_name: str, item_id: str):
        self._invalidate_cache(table_name)
        data = self._load_local_data()
        data[table_name] = [item for item in data.get(table_name, []) if str(item.get("id")) != str(item_id)]
        self._save_local_data(data)

        if self.mode == "supabase" and self.supabase_client:
            try:
                self.supabase_client.table(table_name.lower()).delete().eq("id", item_id).execute()
            except Exception:
                pass
        elif self.mode == "gsheets":
            try:
                ws = self._get_or_create_worksheet(table_name)
                if ws:
                    records = ws.get_all_records()
                    for idx, r in enumerate(records, start=2):
                        if str(r.get("id")) == str(item_id):
                            ws.delete_rows(idx)
                            break
            except Exception:
                pass

    # -------------------------------------------------------------
    # DAILY GOALS
    # -------------------------------------------------------------
    def get_daily_goals(self) -> list:
        records = self._get_table_records("Daily_Goals")
        return [r for r in records if str(r.get("active", "True")).strip().lower() in ["true", "1", "yes", "t", ""]]

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
        self._db_insert("Daily_Goals", new_goal)
        return goal_id

    def delete_daily_goal(self, goal_id: str):
        self._db_delete("Daily_Goals", goal_id)

    # -------------------------------------------------------------
    # DAILY LOG & SCORES
    # -------------------------------------------------------------
    def get_daily_log(self, date_str: str) -> dict:
        """Returns map of goal_id -> bool completion status for date."""
        records = self._get_table_records("Daily_Log")
        date_logs = [r for r in records if str(r.get("date")) == date_str]
        return {r["goal_id"]: str(r.get("completed")).lower() in ["true", "1"] for r in date_logs}

    def toggle_daily_goal(self, goal_id: str, date_str: str, completed: bool):
        self._invalidate_cache("Daily_Log")
        records = self._get_table_records("Daily_Log")
        found_item = None
        for r in records:
            if str(r.get("date")) == date_str and str(r.get("goal_id")) == str(goal_id):
                found_item = r
                break

        if found_item:
            self._db_update("Daily_Log", found_item["id"], {"completed": completed, "updated_at": datetime.datetime.now().isoformat()})
        else:
            log_id = f"log_{int(datetime.datetime.now().timestamp())}"
            new_log = {
                "id": log_id,
                "date": date_str,
                "goal_id": goal_id,
                "completed": completed,
                "updated_at": datetime.datetime.now().isoformat()
            }
            self._db_insert("Daily_Log", new_log)

    def calculate_daily_score(self, date_str: str, goals_list: list = None) -> tuple:
        """Returns (score_percentage, completed_count, total_count)."""
        goals = goals_list if goals_list is not None else self.get_daily_goals()
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
        return self._get_table_records("Tasks")

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
        self._db_insert("Tasks", new_task)
        return task_id

    def update_task_status(self, task_id: str, status: str):
        completed_at = datetime.date.today().strftime("%Y-%m-%d") if status == "Completed" else ""
        self._db_update("Tasks", task_id, {"status": status, "completed_at": completed_at})

    def delete_task(self, task_id: str):
        self._db_delete("Tasks", task_id)
        # Delete associated subtasks
        subtasks = self.get_subtasks(task_id)
        for st in subtasks:
            self.delete_subtask(st["id"])

    def perform_task_rollover(self, today_str: str) -> int:
        rolled_over_count = 0
        tasks = self.get_tasks()
        to_rollover = [t for t in tasks if t.get("status") != "Completed" and t.get("target_date") and t.get("target_date") < today_str]
        for t in to_rollover:
            self._db_update("Tasks", t["id"], {"target_date": today_str})
            rolled_over_count += 1
        return rolled_over_count

    # -------------------------------------------------------------
    # SUBTASKS / MINI-TASKS
    # -------------------------------------------------------------
    def get_subtasks(self, task_id: str) -> list:
        records = self._get_table_records("Subtasks")
        return [r for r in records if str(r.get("task_id")) == str(task_id)]

    def add_subtask(self, task_id: str, title: str) -> str:
        st_id = f"st_{int(datetime.datetime.now().timestamp())}"
        new_st = {
            "id": st_id,
            "task_id": task_id,
            "title": title,
            "completed": False,
            "created_at": datetime.date.today().strftime("%Y-%m-%d")
        }
        self._db_insert("Subtasks", new_st)
        return st_id

    def toggle_subtask(self, subtask_id: str, completed: bool):
        self._db_update("Subtasks", subtask_id, {"completed": completed})

    def delete_subtask(self, subtask_id: str):
        self._db_delete("Subtasks", subtask_id)

    # -------------------------------------------------------------
    # JOURNAL ENTRIES
    # -------------------------------------------------------------
    def get_journal_entry(self, date_str: str) -> dict:
        records = self._get_table_records("Journal_Entries")
        entries = [r for r in records if str(r.get("date")) == date_str]
        return entries[0] if entries else {}

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
        existing = self.get_journal_entry(date_str)
        if existing:
            self._db_update("Journal_Entries", entry_id, entry_data)
        else:
            self._db_insert("Journal_Entries", entry_data)

    # -------------------------------------------------------------
    # NOTES ENGINE
    # -------------------------------------------------------------
    def get_notes(self) -> list:
        return self._get_table_records("Notes")

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
        self._db_insert("Notes", new_note)
        return note_id

    def update_note(self, note_id: str, title: str, category: str, content: str, tags: str = "", is_pinned: bool = False, color: str = "blue"):
        updated_at = datetime.date.today().strftime("%Y-%m-%d")
        self._db_update("Notes", note_id, {
            "title": title,
            "category": category,
            "content": content,
            "tags": tags,
            "is_pinned": is_pinned,
            "color": color,
            "updated_at": updated_at
        })

    def toggle_note_pin(self, note_id: str, is_pinned: bool):
        self._db_update("Notes", note_id, {"is_pinned": is_pinned})

    def delete_note(self, note_id: str):
        self._db_delete("Notes", note_id)
