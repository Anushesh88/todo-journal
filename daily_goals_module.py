import streamlit as st
import datetime
from database import DatabaseManager

def render_daily_goals_tab(db: DatabaseManager, active_date_str: str):
    st.markdown("### 🎯 Daily Goals & Routine Engine")
    st.caption("Daily goals recur automatically every day. Complete them daily to boost your daily score.")

    # Fetch daily goals & logs
    goals = db.get_daily_goals()
    score_pct, completed_cnt, total_cnt = db.calculate_daily_score(active_date_str)

    # -------------------------------------------------------------
    # KPI Score Display
    # -------------------------------------------------------------
    k1, k2, k3 = st.columns([1.5, 1, 1])

    with k1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Daily Completion Score ({active_date_str})</div>
            <div class="metric-value">{score_pct}%</div>
            <div class="metric-subtext">{completed_cnt} of {total_cnt} daily goals completed</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        badge_cls = "badge-green" if score_pct >= 80 else ("badge-amber" if score_pct >= 50 else "badge-red")
        badge_label = "🌟 Excellent" if score_pct >= 80 else ("🔥 Getting There" if score_pct >= 50 else "🌱 Keep Going")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Status Rating</div>
            <div style="margin-top: 0.5rem;"><span class="badge {badge_cls}" style="font-size: 1rem; padding: 0.35rem 0.8rem;">{badge_label}</span></div>
            <div class="metric-subtext">Based on active daily completion</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Active Goals</div>
            <div class="metric-value">{total_cnt}</div>
            <div class="metric-subtext">Recurring daily habits</div>
        </div>
        """, unsafe_allow_html=True)

    # Progress bar
    st.progress(score_pct / 100.0 if total_cnt > 0 else 0.0)
    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # Daily Goals Checklist
    # -------------------------------------------------------------
    c_left, c_right = st.columns([2, 1])

    with c_left:
        st.markdown("#### 📋 Today's Daily Checklist")
        if len(goals) == 0:
            st.info("No daily recurring goals found. Add your first daily goal using the panel on the right!")
        else:
            log_map = db.get_daily_log(active_date_str)
            # Push completed goals to the very end of the stack
            sorted_goals = sorted(goals, key=lambda g: 1 if log_map.get(g["id"], False) else 0)
            for g in sorted_goals:
                gid = g["id"]
                is_completed = log_map.get(gid, False)

                col_chk, col_title, col_del = st.columns([0.1, 0.8, 0.1])
                with col_chk:
                    chk = st.checkbox(
                        label=f"Complete goal {g['title']}",
                        value=is_completed,
                        key=f"chk_goal_{active_date_str}_{gid}",
                        label_visibility="collapsed"
                    )
                    if chk != is_completed:
                        db.toggle_daily_goal(gid, active_date_str, chk)
                        st.rerun()

                with col_title:
                    category_badge = f'<span class="badge badge-purple">{g.get("category", "Habit")}</span>'
                    title_style = "text-decoration: line-through; opacity: 0.6;" if is_completed else "font-weight: 600;"
                    st.markdown(f"""
                    <div style="padding: 0.2rem 0;">
                        <span style="{title_style} font-size: 1rem;">{g['title']}</span>
                        &nbsp; {category_badge}
                    </div>
                    """, unsafe_allow_html=True)

                with col_del:
                    if st.button("🗑️", key=f"del_goal_{gid}", help="Delete daily goal"):
                        db.delete_daily_goal(gid)
                        st.rerun()

    with c_right:
        st.markdown("#### ➕ Add New Daily Goal")
        with st.form("new_daily_goal_form", clear_on_submit=True):
            new_title = st.text_input("Goal Title / Habit", placeholder="e.g. Drink 2L water, Exercise 30m")
            new_cat = st.selectbox("Category", ["Health", "Wellness", "Learning", "Productivity", "Mindset", "Custom"])
            if new_cat == "Custom":
                new_cat = st.text_input("Custom Category", value="Personal")

            submitted = st.form_submit_button("✨ Save Recurring Goal", use_container_width=True)
            if submitted:
                if new_title.strip():
                    db.add_daily_goal(new_title.strip(), new_cat)
                    st.success(f"Added '{new_title}' to recurring daily goals!")
                    st.rerun()
                else:
                    st.warning("Please enter a goal title.")
