"""Streamlit dashboard for University Data Platform."""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from run_pipeline import main as run_pipeline_main
from src.config import FEATURES_DIR, WAREHOUSE_PATH, ensure_directories
from src.semantic_layer import (
    get_faculty_metrics,
    get_group_metrics,
    get_kpi_summary,
    get_lms_engagement,
    get_room_utilization,
    get_student_details,
)
from src.warehouse_loader import run_query

REQUIRED_WAREHOUSE_TABLES = {
    "student_performance_gold",
    "faculty_performance_gold",
    "lms_engagement_gold",
    "room_utilization_gold",
    "student_features",
}


def _existing_tables() -> set[str]:
    """Return table names that currently exist in the DuckDB warehouse."""
    if not WAREHOUSE_PATH.exists():
        return set()

    con = duckdb.connect(str(WAREHOUSE_PATH), read_only=True)
    try:
        rows = con.execute(
            "SELECT table_name FROM information_schema.tables"
        ).fetchall()
        return {row[0] for row in rows}
    finally:
        con.close()


def _warehouse_is_ready() -> bool:
    """Check whether the local warehouse exists and contains dashboard tables."""
    return REQUIRED_WAREHOUSE_TABLES.issubset(_existing_tables())


def _run_pipeline_from_dashboard() -> None:
    """Create all folders, generated data layers, feature store and warehouse."""
    ensure_directories()
    run_pipeline_main()


def _ensure_warehouse_ready() -> bool:
    """Build the warehouse on first cloud launch or offer a manual retry button."""
    if _warehouse_is_ready():
        return True

    st.info(
        "DuckDB warehouse не найден или ещё не заполнен. "
        "Dashboard может создать демонстрационные данные автоматически."
    )

    if "pipeline_attempted" not in st.session_state:
        st.session_state.pipeline_attempted = True
        with st.spinner("Первый запуск: генерируем данные и строим warehouse..."):
            try:
                _run_pipeline_from_dashboard()
            except Exception as exc:  # noqa: BLE001 - show cloud startup errors in UI
                st.session_state.pipeline_error = str(exc)
                st.error("Автоматический запуск pipeline завершился ошибкой.")
                st.exception(exc)
                return False
        st.success("Pipeline завершён, warehouse готов.")
        st.rerun()

    if _warehouse_is_ready():
        return True

    if "pipeline_error" in st.session_state:
        st.warning(
            "Автоматический запуск уже выполнялся, но warehouse всё ещё не готов. "
            "Можно попробовать запустить pipeline вручную кнопкой ниже."
        )

    if st.button("Run pipeline", type="primary"):
        with st.spinner("Запускаем pipeline..."):
            try:
                _run_pipeline_from_dashboard()
            except Exception as exc:  # noqa: BLE001 - show manual retry errors in UI
                st.session_state.pipeline_error = str(exc)
                st.error("Pipeline завершился ошибкой.")
                st.exception(exc)
                return False
        st.success("Pipeline завершён, обновляем dashboard.")
        st.rerun()

    return False


def _table_exists(table_name: str) -> bool:
    """Check if a table exists in the DuckDB warehouse."""
    return table_name in _existing_tables()


def _load_features_preview() -> pd.DataFrame:
    """Load feature store preview from Parquet."""
    path = FEATURES_DIR / "student_features.parquet"
    if path.exists():
        return pd.read_parquet(path).head(20)
    return pd.DataFrame()


def _load_streaming_events(limit: int = 20) -> pd.DataFrame:
    """Load recent streaming events from DuckDB."""
    if not _table_exists("streaming_events"):
        return pd.DataFrame()
    return run_query(
        f"""
        SELECT event_id, student_id, event_type, building_id, room_id, event_time
        FROM streaming_events
        ORDER BY event_time DESC
        LIMIT {limit}
        """
    )


def _load_streaming_metrics() -> dict:
    """Load streaming metrics from DuckDB."""
    if not _table_exists("streaming_metrics"):
        return {}
    df = run_query("SELECT metric_name, metric_value FROM streaming_metrics")
    return dict(zip(df["metric_name"], df["metric_value"]))


def main() -> None:
    """Render the Streamlit dashboard."""
    st.set_page_config(
        page_title="University Data Platform",
        page_icon="🎓",
        layout="wide",
    )

    st.title("University Data Platform Dashboard")

    if not _ensure_warehouse_ready():
        st.stop()

    # Sidebar filters
    st.sidebar.header("Filters")
    faculty_list = run_query(
        "SELECT DISTINCT faculty FROM student_performance_gold ORDER BY faculty"
    )["faculty"].tolist()
    selected_faculty = st.sidebar.selectbox(
        "Faculty", ["All"] + faculty_list
    )

    faculty_filter = None if selected_faculty == "All" else selected_faculty

    if faculty_filter:
        groups = run_query(
            f"""
            SELECT DISTINCT group_id FROM student_performance_gold
            WHERE faculty = '{faculty_filter}' ORDER BY group_id
            """
        )["group_id"].tolist()
    else:
        groups = []

    selected_group = st.sidebar.selectbox(
        "Group", ["All"] + groups if groups else ["All"]
    )
    group_filter = None if selected_group == "All" else selected_group

    show_streaming = st.sidebar.checkbox("Show streaming metrics", value=True)

    if st.sidebar.button("Refresh data"):
        st.cache_data.clear()
        st.rerun()

    # KPI cards
    kpi = get_kpi_summary()
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Students", kpi.get("total_students", 0))
    col2.metric("Average Grade", kpi.get("avg_grade", 0))
    col3.metric("At-Risk Students", kpi.get("risk_students", 0))
    col4.metric("Risk Share", f"{kpi.get('risk_students_share', 0):.1%}")
    col5.metric("Avg Completion Rate", f"{kpi.get('avg_completion_rate', 0):.1%}")

    st.divider()

    # Faculty charts
    st.subheader("Faculty Analytics")
    faculty_df = get_faculty_metrics()

    chart_col1, chart_col2, chart_col3 = st.columns(3)

    with chart_col1:
        fig_grade = px.bar(
            faculty_df,
            x="faculty",
            y="avg_grade",
            title="Average Grade by Faculty",
            color="faculty",
        )
        st.plotly_chart(fig_grade, use_container_width=True)

    with chart_col2:
        fig_risk = px.bar(
            faculty_df,
            x="faculty",
            y="risk_students_share",
            title="Risk Share by Faculty",
            color="faculty",
        )
        st.plotly_chart(fig_risk, use_container_width=True)

    with chart_col3:
        completion_df = run_query(
            """
            SELECT faculty, ROUND(avg_completion_rate, 4) AS avg_completion_rate
            FROM faculty_performance_gold
            ORDER BY faculty
            """
        )
        fig_completion = px.bar(
            completion_df,
            x="faculty",
            y="avg_completion_rate",
            title="Completion Rate by Faculty",
            color="faculty",
        )
        st.plotly_chart(fig_completion, use_container_width=True)

    st.divider()

    # Drill-down section
    st.subheader("Drill-down: Faculty → Group → Students")

    group_df = get_group_metrics(faculty_filter)
    if not group_df.empty:
        fig_groups = px.bar(
            group_df,
            x="group_id",
            y="avg_grade",
            color="faculty",
            title="Average Grade by Group",
        )
        st.plotly_chart(fig_groups, use_container_width=True)
        st.dataframe(group_df, use_container_width=True)

    students_df = get_student_details(faculty_filter, group_filter)
    st.subheader("Student Details")
    st.dataframe(students_df, use_container_width=True)

    st.divider()

    # Engagement and rooms
    col_eng, col_room = st.columns(2)

    with col_eng:
        st.subheader("LMS Engagement")
        lms_df = get_lms_engagement()
        if not lms_df.empty:
            fig_lms = px.histogram(
                lms_df,
                x="engagement_score",
                nbins=30,
                title="Engagement Score Distribution",
            )
            st.plotly_chart(fig_lms, use_container_width=True)

            activity_summary = run_query(
                """
                SELECT 'login' AS activity_type, SUM(login_count) AS count
                FROM lms_engagement_gold
                UNION ALL
                SELECT 'course_view', SUM(course_view_count) FROM lms_engagement_gold
                UNION ALL
                SELECT 'material_download', SUM(material_download_count)
                FROM lms_engagement_gold
                UNION ALL
                SELECT 'forum_post', SUM(forum_post_count) FROM lms_engagement_gold
                """
            )
            fig_activity = px.pie(
                activity_summary,
                names="activity_type",
                values="count",
                title="LMS Events by Type",
            )
            st.plotly_chart(fig_activity, use_container_width=True)

    with col_room:
        st.subheader("Room Utilization")
        room_df = get_room_utilization()
        if not room_df.empty:
            fig_room = px.bar(
                room_df.head(15),
                x="room_id",
                y="utilization_rate",
                color="building_id",
                title="Top 15 Rooms by Utilization Rate",
            )
            st.plotly_chart(fig_room, use_container_width=True)
            st.dataframe(room_df, use_container_width=True)

    st.divider()

    # Feature store preview
    st.subheader("Feature Store Preview")
    features_preview = _load_features_preview()
    if not features_preview.empty:
        st.dataframe(features_preview, use_container_width=True)
    else:
        st.info("Feature store not available. Run pipeline first.")

    st.divider()

    # Streaming section
    st.subheader("Streaming Analytics")
    if show_streaming:
        if _table_exists("streaming_events"):
            metrics = _load_streaming_metrics()
            events_df = _load_streaming_events()

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(
                "Events / Minute",
                f"{metrics.get('events_per_minute', 0):.0f}",
            )
            m2.metric(
                "Active Students (5 min)",
                f"{metrics.get('active_students_last_5_min', 0):.0f}",
            )
            m3.metric(
                "Assignment Submissions (5 min)",
                f"{metrics.get('assignment_submissions_last_5_min', 0):.0f}",
            )
            m4.metric(
                "Building Entries (5 min)",
                f"{metrics.get('building_entries_last_5_min', 0):.0f}",
            )

            if not events_df.empty:
                st.write("Last 20 streaming events:")
                st.dataframe(events_df, use_container_width=True)
        else:
            st.warning(
                "Streaming data is not available yet. "
                "Run `python run_streaming_demo.py`"
            )


if __name__ == "__main__":
    main()
