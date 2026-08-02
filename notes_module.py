import streamlit as st
import datetime
from database import DatabaseManager

COLOR_MAP = {
    "Blue": "badge-blue",
    "Green": "badge-green",
    "Amber": "badge-amber",
    "Purple": "badge-purple",
    "Red": "badge-red"
}

def render_notes_tab(db: DatabaseManager):
    st.markdown("### 📝 Notes & Idea Hub")
    st.caption("Organize your thoughts, code snippets, meeting minutes, and project ideas with markdown support and tagging.")

    notes = db.get_notes()

    # -------------------------------------------------------------
    # Top Filter Bar (Task Manager Style)
    # -------------------------------------------------------------
    f1, f2, f3 = st.columns([1.2, 1.2, 1.2])

    categories = list(set([n.get("category", "General") for n in notes])) if notes else []
    categories.sort()
    categories.insert(0, "All Categories")

    with f1:
        selected_cat = st.selectbox("Category Filter", categories, key="notes_cat_filter")
    with f2:
        search_q = st.text_input("🔍 Search Notes", placeholder="Search by title, tag, or content...", key="notes_search_q")
    with f3:
        pinned_only = st.checkbox("📌 Pinned Only", value=False, key="notes_pinned_only")

    # Apply Filtering
    filtered_notes = []
    for n in notes:
        if selected_cat != "All Categories" and n.get("category") != selected_cat:
            continue
        if pinned_only and not n.get("is_pinned", False):
            continue
        if search_q:
            q = search_q.lower()
            in_title = q in str(n.get("title", "")).lower()
            in_content = q in str(n.get("content", "")).lower()
            in_tags = q in str(n.get("tags", "")).lower()
            if not (in_title or in_content or in_tags):
                continue
        filtered_notes.append(n)

    # Separate pinned vs regular notes
    pinned_notes = [n for n in filtered_notes if n.get("is_pinned", False)]
    other_notes = [n for n in filtered_notes if not n.get("is_pinned", False)]

    n_col1, n_col2 = st.columns([2.2, 1.2])

    with n_col1:
        st.markdown(f"#### 📚 Saved Notes ({len(filtered_notes)})")
        if not filtered_notes:
            st.info("No notes found matching your filter criteria. Create a new note using the form on the right!")
        else:
            # Helper function to render a note card
            def render_note_card(note: dict):
                nid = note["id"]
                title = note.get("title", "Untitled Note")
                cat = note.get("category", "General")
                content = note.get("content", "")
                tags = note.get("tags", "")
                is_pinned = note.get("is_pinned", False)
                color = note.get("color", "blue").capitalize()
                badge_cls = COLOR_MAP.get(color, "badge-blue")
                created_at = note.get("created_at", "")

                with st.container():
                    st.markdown(f"""
                    <div class="item-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span class="badge {badge_cls}">{cat}</span>
                                {f'<span class="badge badge-amber">📌 Pinned</span>' if is_pinned else ''}
                                {f'<span style="font-size: 0.75rem; color: #a1a1aa; margin-left: 0.5rem;">#{tags}</span>' if tags else ''}
                            </div>
                            <div style="font-size: 0.78rem; color: #71717a;">
                                🕒 {created_at}
                            </div>
                        </div>
                        <div style="margin-top: 0.5rem; font-size: 1.1rem; font-weight: 700;">
                            {title}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Quick Preview / Expandable Full Note
                    with st.expander("📄 View / Edit Note Content", expanded=False):
                        tab_read, tab_edit = st.tabs(["📖 Reading Mode", "✏️ Edit Note"])
                        
                        with tab_read:
                            st.markdown(content if content else "*No content written yet.*")

                        with tab_edit:
                            with st.form(key=f"edit_note_form_{nid}"):
                                e_title = st.text_input("Title", value=title)
                                e_cat = st.text_input("Category", value=cat)
                                e_tags = st.text_input("Tags (comma separated)", value=tags)
                                e_color = st.selectbox("Color Theme", ["Blue", "Green", "Amber", "Purple", "Red"], index=["Blue", "Green", "Amber", "Purple", "Red"].index(color) if color in ["Blue", "Green", "Amber", "Purple", "Red"] else 0)
                                e_pinned = st.checkbox("Pin Note to Top", value=is_pinned)
                                e_content = st.text_area("Content (Markdown supported)", value=content, height=180)

                                save_note_sub = st.form_submit_button("💾 Save Changes", use_container_width=True)
                                if save_note_sub:
                                    db.update_note(
                                        note_id=nid,
                                        title=e_title,
                                        category=e_cat,
                                        content=e_content,
                                        tags=e_tags,
                                        is_pinned=e_pinned,
                                        color=e_color
                                    )
                                    st.success("Note updated!")
                                    st.rerun()

                    # Action controls row
                    c1, c2, c3 = st.columns([1, 1, 0.4])
                    with c1:
                        pin_label = "📌 Unpin Note" if is_pinned else "📌 Pin Note"
                        if st.button(pin_label, key=f"pin_btn_{nid}"):
                            db.toggle_note_pin(nid, not is_pinned)
                            st.rerun()

                    with c2:
                        st.download_button(
                            label="📥 Export Note (.md)",
                            data=f"# {title}\n\n**Category:** {cat}\n**Tags:** {tags}\n\n---\n\n{content}",
                            file_name=f"{title.replace(' ', '_').lower()}.md",
                            mime="text/markdown",
                            key=f"dl_note_{nid}"
                        )

                    with c3:
                        if st.button("🗑️", key=f"del_note_{nid}"):
                            db.delete_note(nid)
                            st.rerun()

                    st.markdown("<hr style='margin: 0.8rem 0; border: 0; border-top: 1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

            # Render Pinned Notes first
            if pinned_notes:
                st.markdown("##### 📌 Pinned Notes")
                for n in pinned_notes:
                    render_note_card(n)

            # Render Other Notes
            if other_notes:
                st.markdown("##### 📁 Other Notes")
                for n in other_notes:
                    render_note_card(n)

    with n_col2:
        st.markdown("#### ➕ Create New Note")
        with st.form("create_note_form", clear_on_submit=True):
            n_title = st.text_input("Note Title", placeholder="e.g. Brainstorming session notes")
            n_cat = st.selectbox("Category", ["Ideas", "Meeting", "Quick Draft", "Study", "Technical", "Personal", "Custom"])
            if n_cat == "Custom":
                n_cat = st.text_input("Custom Category Name", value="General")

            n_tags = st.text_input("Tags", placeholder="e.g. project, sprint1, python")
            n_color = st.selectbox("Color Theme Badge", ["Blue", "Green", "Amber", "Purple", "Red"])
            n_pinned = st.checkbox("📌 Pin to Top immediately", value=False)

            n_content = st.text_area("Note Content (Markdown supported)", placeholder="Type your notes here...", height=200)

            sub_create_note = st.form_submit_button("✨ Save Note", use_container_width=True)

            if sub_create_note:
                if n_title.strip():
                    db.add_note(
                        title=n_title.strip(),
                        category=n_cat,
                        content=n_content,
                        tags=n_tags,
                        is_pinned=n_pinned,
                        color=n_color
                    )
                    st.success(f"Note '{n_title}' created successfully!")
                    st.rerun()
                else:
                    st.warning("Please enter a note title.")
