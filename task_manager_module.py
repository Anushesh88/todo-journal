import streamlit as st
import datetime
from database import DatabaseManager
from calendar_sync import generate_gcal_url, generate_ics_content

def render_task_manager_tab(db: DatabaseManager, active_date_str: str):
    st.markdown("### 📌 Task Manager & Strategic Planner")
    st.caption("Manage Short-Term and Long-Term tasks with deadlines, subtasks, auto-rollover, and optional Google Calendar sync.")

    # Execute auto-rollover check for overdue unfulfilled tasks
    rolled_cnt = db.perform_task_rollover(active_date_str)
    if rolled_cnt > 0:
        st.markdown(f"""
        <div class="rollover-banner">
            🚀 <strong>Automatic Rollover:</strong> {rolled_cnt} unfulfilled task(s) from past dates were automatically passed forward to today ({active_date_str})!
        </div>
        """, unsafe_allow_html=True)

    tasks = db.get_tasks()

    # Filter section
    col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
    with col_f1:
        type_filter = st.selectbox("Task Type", ["All Types", "Short-Term", "Long-Term"])
    with col_f2:
        status_filter = st.selectbox("Status", ["All", "Pending", "In Progress", "Completed"])
    with col_f3:
        search_query = st.text_input("🔍 Search Tasks", placeholder="Type to search...")

    # Apply filters
    filtered_tasks = []
    for t in tasks:
        if type_filter != "All Types" and t.get("type") != type_filter:
            continue
        if status_filter != "All" and t.get("status") != status_filter:
            continue
        if search_query and search_query.lower() not in t.get("title", "").lower():
            continue
        filtered_tasks.append(t)

    t_col1, t_col2 = st.columns([2.2, 1.2])

    with t_col1:
        st.markdown(f"#### 📝 Task List ({len(filtered_tasks)})")
        if not filtered_tasks:
            st.info("No tasks found matching your filters. Create a new task using the form!")
        else:
            for task in filtered_tasks:
                tid = task["id"]
                title = task.get("title", "")
                task_type = task.get("type", "Short-Term")
                priority = task.get("priority", "Medium")
                status = task.get("status", "Pending")
                deadline = task.get("deadline", "")
                is_longterm = task.get("is_longterm", False) or (task_type == "Long-Term")
                is_completed = status == "Completed"

                # Subtask data
                subtasks = db.get_subtasks(tid) if is_longterm else []
                sub_completed = sum(1 for st_item in subtasks if st_item.get("completed", False))
                sub_total = len(subtasks)
                sub_pct = int((sub_completed / sub_total) * 100) if sub_total > 0 else 0

                # Priority Badge
                p_cls = "badge-red" if priority == "High" else ("badge-amber" if priority == "Medium" else "badge-blue")
                type_cls = "badge-purple" if is_longterm else "badge-blue"

                with st.container():
                    st.markdown(f"""
                    <div class="item-card {'completed' if is_completed else ''}">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <span class="badge {type_cls}">{task_type}</span>
                                <span class="badge {p_cls}">{priority} Priority</span>
                                <span class="badge {'badge-green' if is_completed else 'badge-amber'}">{status}</span>
                            </div>
                            <div style="font-size: 0.8rem; color: #71717a;">
                                📅 Deadline: <strong>{deadline}</strong>
                            </div>
                        </div>
                        <div style="margin-top: 0.6rem; font-size: 1.05rem; font-weight: 700;">
                            {title}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Controls row
                    c1, c2, c3, c4 = st.columns([1.2, 1, 1, 0.4])

                    with c1:
                        new_status = st.selectbox(
                            "Status",
                            ["Pending", "In Progress", "Completed"],
                            index=["Pending", "In Progress", "Completed"].index(status) if status in ["Pending", "In Progress", "Completed"] else 0,
                            key=f"status_sel_{tid}",
                            label_visibility="collapsed"
                        )
                        if new_status != status:
                            db.update_task_status(tid, new_status)
                            st.rerun()

                    with c2:
                        # Optional Google Calendar Sync link controls
                        show_cal = task.get("calendar_synced", True)
                        if show_cal:
                            gcal_url = generate_gcal_url(
                                title=f"[{task_type}] {title}",
                                details=f"Task Priority: {priority}\nTarget Date: {task.get('target_date')}\nDeadline: {deadline}\nSubtasks: {sub_total}",
                                start_date=task.get("target_date", active_date_str),
                                end_date=deadline
                            )
                            st.markdown(f'<a href="{gcal_url}" target="_blank" style="text-decoration:none;"><button style="background: rgba(59, 130, 246, 0.15); color: #3b82f6; border: 1px solid #3b82f6; border-radius: 6px; padding: 5px 12px; font-size: 0.82rem; font-weight: 600; cursor: pointer;">📅 Google Cal Link</button></a>', unsafe_allow_html=True)
                        else:
                            st.caption("Calendar Unlinked")

                    with c3:
                        if show_cal:
                            ics_data = generate_ics_content(title, f"Priority: {priority}\nDeadline: {deadline}", task.get("target_date", active_date_str), deadline)
                            st.download_button(
                                label="📥 .ICS File",
                                data=ics_data,
                                file_name=f"{title.replace(' ', '_')}.ics",
                                mime="text/calendar",
                                key=f"ics_dl_{tid}"
                            )

                    with c4:
                        if st.button("🗑️", key=f"del_task_{tid}"):
                            db.delete_task(tid)
                            st.rerun()

                    # Subtasks section for Long-Term Tasks
                    if is_longterm:
                        with st.expander(f"🧩 Subtasks / Mini-Tasks ({sub_completed}/{sub_total}) - {sub_pct}% Done", expanded=not is_completed):
                            if sub_total > 0:
                                st.progress(sub_pct / 100.0)

                            for st_item in subtasks:
                                st_id = st_item["id"]
                                st_comp = st_item.get("completed", False)
                                s_c1, s_c2, s_c3 = st.columns([0.1, 0.8, 0.1])
                                with s_c1:
                                    st_chk = st.checkbox(label=f"Complete subtask {st_item['title']}", value=st_comp, key=f"st_chk_{st_id}", label_visibility="collapsed")
                                    if st_chk != st_comp:
                                        db.toggle_subtask(st_id, st_chk)
                                        st.rerun()
                                with s_c2:
                                    st_style = "text-decoration: line-through; opacity: 0.6;" if st_comp else ""
                                    st.markdown(f"<span style='{st_style} font-size: 0.9rem;'>{st_item['title']}</span>", unsafe_allow_html=True)
                                with s_c3:
                                    if st.button("❌", key=f"st_del_{st_id}"):
                                        db.delete_subtask(st_id)
                                        st.rerun()

                            # Add mini task inline input
                            with st.form(key=f"add_subtask_form_{tid}", clear_on_submit=True):
                                sub_title = st.text_input("Add Mini Task", placeholder="e.g. Draft chapter 1, Prepare slide deck", label_visibility="collapsed")
                                sub_sub = st.form_submit_button("➕ Add Mini Task", use_container_width=True)
                                if sub_sub and sub_title.strip():
                                    db.add_subtask(tid, sub_title.strip())
                                    st.rerun()

                    st.markdown("<hr style='margin: 0.8rem 0; border: 0; border-top: 1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

    with t_col2:
        st.markdown("#### ➕ Create New Task")
        with st.form("create_task_form", clear_on_submit=True):
            t_title = st.text_input("Task Title", placeholder="e.g. Submit quarterly report")
            t_type = st.radio("Task Duration Type", ["Short-Term", "Long-Term"], horizontal=True)
            t_cat = st.selectbox("Category", ["Work", "Development", "Personal", "Health", "Finance", "Study"])
            t_priority = st.select_slider("Priority Level", options=["Low", "Medium", "High"], value="Medium")

            t_target_date = st.date_input("Target Execution Date", datetime.date.today())
            t_deadline = st.date_input("Final Deadline", datetime.date.today() + datetime.timedelta(days=3))

            st.markdown("##### 📅 Google Calendar Preference")
            sync_cal = st.checkbox("Link Task to Google Calendar", value=True, help="Optionally link task to Google Calendar")

            sub_task_create = st.form_submit_button("🚀 Create Task", use_container_width=True)

            if sub_task_create:
                if t_title.strip():
                    is_lt = (t_type == "Long-Term")
                    target_str = t_target_date.strftime("%Y-%m-%d")
                    deadline_str = t_deadline.strftime("%Y-%m-%d")
                    tid = db.add_task(
                        title=t_title.strip(),
                        task_type=t_type,
                        category=t_cat,
                        priority=t_priority,
                        target_date=target_str,
                        deadline=deadline_str,
                        is_longterm=is_lt
                    )
                    st.success(f"Task '{t_title}' created successfully!")

                    if sync_cal:
                        cal_link = generate_gcal_url(
                            title=f"[{t_type}] {t_title.strip()}",
                            details=f"Category: {t_cat}\nPriority: {t_priority}\nTarget Date: {target_str}\nDeadline: {deadline_str}",
                            start_date=target_str,
                            end_date=deadline_str
                        )
                        st.markdown(f"""
                        <div style="margin-top: 0.5rem; padding: 0.8rem; background: rgba(59, 130, 246, 0.1); border: 1px solid #3b82f6; border-radius: 8px;">
                            📅 <strong>Google Calendar Link Ready:</strong><br>
                            <a href="{cal_link}" target="_blank" style="display: inline-block; margin-top: 0.4rem; padding: 0.35rem 0.8rem; background: #3b82f6; color: white; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 0.85rem;">
                                ➕ Add Task to Google Calendar
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.warning("Task title cannot be empty.")
