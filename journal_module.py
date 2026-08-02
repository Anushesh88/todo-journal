import streamlit as st
import datetime
from database import DatabaseManager

MOOD_OPTIONS = [
    ("😊 Happy & Energized", "Happy"),
    ("🚀 Highly Productive", "Productive"),
    ("🧘 Mindful & Calm", "Calm"),
    ("😐 Neutral / Balanced", "Neutral"),
    ("😴 Tired / Low Energy", "Tired"),
    ("🔥 On Fire / Focused", "Focused")
]

def render_journal_tab(db: DatabaseManager, active_date_str: str):
    st.markdown("### 📖 Daily Reflection & Journal")
    st.caption(f"Reflect on your achievements, mood, and learnings for {active_date_str}.")

    # Load existing entry if available
    entry = db.get_journal_entry(active_date_str)
    score_pct, completed_cnt, total_cnt = db.calculate_daily_score(active_date_str)

    j_col1, j_col2 = st.columns([2, 1])

    with j_col1:
        with st.form("journal_entry_form"):
            st.markdown("#### 💭 Reflection Entry")
            
            # Mood selection
            mood_labels = [m[0] for m in MOOD_OPTIONS]
            curr_mood = entry.get("mood", mood_labels[0])
            mood_idx = mood_labels.index(curr_mood) if curr_mood in mood_labels else 0
            
            selected_mood = st.selectbox("How did you feel today?", mood_labels, index=mood_idx)

            main_text = st.text_area(
                "Daily Journal & Thoughts",
                value=entry.get("main_text", ""),
                height=180,
                placeholder="What went well today? What challenges did you face? What did you learn?"
            )

            wins_text = st.text_area(
                "🏆 Key Accomplishments & Wins",
                value=entry.get("wins", ""),
                height=100,
                placeholder="List 2-3 highlights or wins from today..."
            )

            gratitude_text = st.text_area(
                "🙏 Gratitude & Positive Moments",
                value=entry.get("gratitude", ""),
                height=90,
                placeholder="What are 3 things you are grateful for today?"
            )

            saved = st.form_submit_button("💾 Save Journal Entry", use_container_width=True)

            if saved:
                db.save_journal_entry(
                    date_str=active_date_str,
                    mood=selected_mood,
                    main_text=main_text,
                    wins=wins_text,
                    gratitude=gratitude_text,
                    score_pct=score_pct
                )
                st.success(f"Journal entry for {active_date_str} saved successfully!")
                st.rerun()

    with j_col2:
        st.markdown("#### 📊 Today's Snapshot")
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Daily Goal Score</div>
            <div class="metric-value">{score_pct}%</div>
            <div class="metric-subtext">{completed_cnt}/{total_cnt} goals completed</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if entry:
            st.markdown("##### 📜 Existing Record")
            st.markdown(f"**Mood:** {entry.get('mood', 'N/A')}")
            st.markdown(f"**Last Updated:** {entry.get('created_at', 'N/A')[:10]}")
            if entry.get('main_text'):
                st.info(f"\"{entry.get('main_text')[:120]}...\"")
        else:
            st.warning("No journal entry saved for this date yet. Fill in the form on the left!")
