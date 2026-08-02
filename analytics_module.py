import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
from database import DatabaseManager

def render_analytics_tab(db: DatabaseManager, is_dark: bool):
    st.markdown("### 📊 Performance Analytics & Productivity Insights")
    st.caption("Track your daily score trends, completion rates, and goal consistency over time.")

    tasks = db.get_tasks()
    goals = db.get_daily_goals()

    # Calculate last 14 days scores
    dates = [(datetime.date.today() - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(13, -1, -1)]
    score_data = []
    for d in dates:
        pct, comp, total = db.calculate_daily_score(d, goals_list=goals)
        score_data.append({"Date": d, "Score": pct, "Completed": comp, "Total": total})

    df_scores = pd.DataFrame(score_data)

    # -------------------------------------------------------------
    # Line Chart: 14-Day Daily Score Trend
    # -------------------------------------------------------------
    st.markdown("""
    <div class="chart-container">
        <div class="chart-title">14-Day Daily Goal Completion Score (%)</div>
        <div class="chart-subtitle">Daily score trend reflecting consistent habit execution</div>
    """, unsafe_allow_html=True)

    fig_score = px.line(
        df_scores,
        x="Date",
        y="Score",
        markers=True,
        text="Score",
        color_discrete_sequence=["#3b82f6"]
    )
    fig_score.update_traces(
        line=dict(width=3),
        marker=dict(size=8, color="#8b5cf6"),
        textposition="top center"
    )
    
    font_color = "#fafafa" if is_dark else "#0f172a"
    grid_color = "rgba(255,255,255,0.06)" if is_dark else "rgba(0,0,0,0.06)"

    fig_score.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color=font_color, size=11),
        margin=dict(l=10, r=10, t=20, b=10),
        yaxis=dict(range=[0, 105], gridcolor=grid_color, title="Score %"),
        xaxis=dict(gridcolor=grid_color, title="Date")
    )

    st.plotly_chart(fig_score, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # Distribution Charts: Tasks Breakdown
    # -------------------------------------------------------------
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
        <div class="chart-container">
            <div class="chart-title">Task Status Distribution</div>
            <div class="chart-subtitle">Breakdown of pending vs completed tasks</div>
        """, unsafe_allow_html=True)

        if tasks:
            df_tasks = pd.DataFrame(tasks)
            status_counts = df_tasks["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]

            fig_donut = px.pie(
                status_counts,
                values="Count",
                names="Status",
                hole=0.5,
                color="Status",
                color_discrete_map={
                    "Completed": "#22c55e",
                    "In Progress": "#f59e0b",
                    "Pending": "#ef4444"
                }
            )
            fig_donut.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="DM Sans, sans-serif", color=font_color),
                margin=dict(l=10, r=10, t=10, b=10)
            )
            st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No task data available for chart.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="chart-container">
            <div class="chart-title">Tasks by Type (Short-Term vs Long-Term)</div>
            <div class="chart-subtitle">Strategic balance between short and long range goals</div>
        """, unsafe_allow_html=True)

        if tasks:
            type_counts = df_tasks["type"].value_counts().reset_index()
            type_counts.columns = ["Type", "Count"]

            fig_type = px.bar(
                type_counts,
                x="Type",
                y="Count",
                color="Type",
                color_discrete_map={
                    "Short-Term": "#3b82f6",
                    "Long-Term": "#a855f7"
                },
                text="Count"
            )
            fig_type.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="DM Sans, sans-serif", color=font_color),
                margin=dict(l=10, r=10, t=10, b=10),
                yaxis=dict(gridcolor=grid_color),
                xaxis=dict(gridcolor=grid_color)
            )
            st.plotly_chart(fig_type, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No task data available for chart.")
        st.markdown("</div>", unsafe_allow_html=True)
