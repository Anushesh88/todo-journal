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
        type_filter = st.selectbox("Task Type", ["All Types", "Today's Task", "Short-Term", "Long-Term"])
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

    # Push completed tasks to the very end of the stack
    filtered_tasks.sort(key=lambda t: 1 if t.get("status") == "Completed" else 0)

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

                # Subtask data for ALL task types
                subtasks = db.get_subtasks(tid)
                sub_completed = sum(1 for st_item in subtasks if st_item.get("completed", False))
                sub_total = len(subtasks)
                sub_pct = int((sub_completed / sub_total) * 100) if sub_total > 0 else 0

                # Priority Badge & CSS styling
                p_cls = "badge-red" if priority == "High" else ("badge-amber" if priority == "Medium" else "badge-blue")
                type_cls = "badge-green" if task_type == "Today's Task" else ("badge-purple" if is_longterm else "badge-blue")

                # Single unified card container
                with st.container(border=True):
                    # Header: Badges & Deadline
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <span class="badge {type_cls}">{task_type}</span>
                            <span class="badge {p_cls}">{priority} Priority</span>
                            <span class="badge {'badge-green' if is_completed else 'badge-amber'}">{status}</span>
                        </div>
                        <div style="font-size: 0.82rem; color: #71717a;">
                            📅 Deadline: <strong>{deadline}</strong>
                        </div>
                    </div>
                    <div style="margin: 0.6rem 0 0.8rem 0; font-size: 1.08rem; font-weight: 700;">
                        {title}
                    </div>
                    """, unsafe_allow_html=True)

                    # Controls row (Status, GCal, ICS, Subtask toggle, Delete)
                    c_cols = [1.2, 1, 1, 0.8, 0.4] if task_type != "Today's Task" else [1.2, 1, 1, 0.4]
                    cols = st.columns(c_cols)

                    with cols[0]:
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

                    with cols[1]:
                        show_cal = task.get("calendar_synced", True)
                        if show_cal:
                            gcal_url = generate_gcal_url(
                                title=f"[{task_type}] {title}",
                                details=f"Task Priority: {priority}\nTarget Date: {task.get('target_date')}\nDeadline: {deadline}\nSubtasks: {sub_total}",
                                start_date=task.get("target_date", active_date_str),
                                end_date=deadline
                            )
                            st.markdown(f'<a href="{gcal_url}" target="_blank" style="text-decoration:none;"><button style="width:100%; background: rgba(59, 130, 246, 0.15); color: #3b82f6; border: 1px solid #3b82f6; border-radius: 6px; padding: 5px 8px; font-size: 0.8rem; font-weight: 600; cursor: pointer;">📅 GCal Link</button></a>', unsafe_allow_html=True)
                        else:
                            st.caption("Calendar Unlinked")

                    with cols[2]:
                        if show_cal:
                            ics_data = generate_ics_content(title, f"Priority: {priority}\nDeadline: {deadline}", task.get("target_date", active_date_str), deadline)
                            st.download_button(
                                label="📥 .ICS",
                                data=ics_data,
                                file_name=f"{title.replace(' ', '_')}.ics",
                                mime="text/calendar",
                                key=f"ics_dl_{tid}",
                                use_container_width=True
                            )

                    # Subtasks toggle button beside delete button
                    if task_type != "Today's Task":
                        with cols[3]:
                            sub_btn_label = f"🧩 Subtasks ({sub_total})"
                            if st.button(sub_btn_label, key=f"btn_toggle_subtasks_{tid}", use_container_width=True):
                                # Toggle session state flag
                                current_flag = st.session_state.get(f"show_subtasks_{tid}", (sub_total > 0))
                                st.session_state[f"show_subtasks_{tid}"] = not current_flag
                                st.rerun()

                        del_col = cols[4]
                    else:
                        del_col = cols[3]

                    with del_col:
                        if st.button("🗑️", key=f"del_task_{tid}"):
                            db.delete_task(tid)
                            st.rerun()

                    # Subtasks section toggled EXCLUSIVELY by the Subtasks button beside delete
                    if task_type != "Today's Task":
                        # Keep open if subtasks exist OR if explicitly toggled by user
                        default_expanded = (sub_total > 0)
                        is_expanded = st.session_state.get(f"show_subtasks_{tid}", default_expanded)

                        if is_expanded:
                            st.markdown("<div style='margin-top: 0.8rem; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 0.6rem;'></div>", unsafe_allow_html=True)
                            if sub_total > 0:
                                st.caption(f"🧩 Subtasks ({sub_completed}/{sub_total}) - {sub_pct}% Completed")
                                st.progress(sub_pct / 100.0)

                            for st_item in subtasks:
                                st_id = st_item["id"]
                                st_comp = st_item.get("completed", False)
                                s_c1, s_c2, s_c3 = st.columns([0.08, 0.84, 0.08])
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

                            # Add mini task inline input form
                            with st.form(key=f"add_subtask_form_{tid}", clear_on_submit=True):
                                sub_title = st.text_input("Add Mini Task", placeholder="e.g. Draft chapter 1, Prepare slide deck", label_visibility="collapsed")
                                sub_sub = st.form_submit_button("➕ Add Mini Task", use_container_width=True)
                                if sub_sub and sub_title.strip():
                                    db.add_subtask(tid, sub_title.strip())
                                    st.session_state[f"show_subtasks_{tid}"] = True
                                    st.rerun()

    with t_col2:
        st.markdown("#### ➕ Create New Task")
        with st.form("create_task_form", clear_on_submit=True):
            t_title = st.text_input("Task Title", placeholder="e.g. Submit quarterly report")
            t_type = st.radio("Task Duration Type", ["Today's Task", "Short-Term", "Long-Term"], horizontal=True, help="Today's Task is a single-day task for today.")
            t_cat = st.selectbox("Category", ["Work", "Development", "Personal", "Health", "Finance", "Study"])
            t_priority = st.select_slider("Priority Level", options=["Low", "Medium", "High"], value="Medium")

            default_target = datetime.datetime.strptime(active_date_str, "%Y-%m-%d").date() if active_date_str else datetime.date.today()
            t_target_date = st.date_input("Target Execution Date", default_target)
            t_deadline = st.date_input("Final Deadline", default_target if t_type == "Today's Task" else default_target + datetime.timedelta(days=3))

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
