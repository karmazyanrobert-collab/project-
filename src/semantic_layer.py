"""Semantic layer: business metrics and KPI queries over DuckDB."""

import pandas as pd

from src.warehouse_loader import run_query


def get_kpi_summary() -> dict:
    """Return top-level KPI summary metrics."""
    df = run_query(
        """
        SELECT
            COUNT(*) AS total_students,
            ROUND(AVG(avg_grade), 2) AS avg_grade,
            SUM(risk_flag) AS risk_students,
            ROUND(SUM(risk_flag) * 1.0 / COUNT(*), 4) AS risk_students_share,
            ROUND(AVG(completion_rate), 4) AS avg_completion_rate
        FROM student_performance_gold
        """
    )
    if df.empty:
        return {}
    row = df.iloc[0]
    return {
        "total_students": int(row["total_students"]),
        "avg_grade": float(row["avg_grade"]),
        "risk_students": int(row["risk_students"]),
        "risk_students_share": float(row["risk_students_share"]),
        "avg_completion_rate": float(row["avg_completion_rate"]),
    }


def get_faculty_metrics() -> pd.DataFrame:
    """Return performance metrics aggregated by faculty."""
    return run_query(
        """
        SELECT
            faculty,
            students_count,
            ROUND(avg_grade, 2) AS avg_grade,
            risk_students_count,
            ROUND(risk_students_share, 4) AS risk_students_share
        FROM faculty_performance_gold
        ORDER BY faculty
        """
    )


def get_group_metrics(faculty: str | None = None) -> pd.DataFrame:
    """Return performance metrics aggregated by faculty and group."""
    sql = """
        SELECT
            faculty,
            group_id,
            COUNT(*) AS students_count,
            ROUND(AVG(avg_grade), 2) AS avg_grade,
            SUM(risk_flag) AS risk_students_count
        FROM student_performance_gold
    """
    if faculty:
        sql += f" WHERE faculty = '{faculty}'"
    sql += " GROUP BY faculty, group_id ORDER BY faculty, group_id"
    return run_query(sql)


def get_student_details(
    faculty: str | None = None, group_id: str | None = None
) -> pd.DataFrame:
    """Return detailed student records with performance and engagement."""
    sql = """
        SELECT
            sp.student_id,
            sp.full_name,
            sp.faculty,
            sp.group_id,
            ROUND(sp.avg_grade, 2) AS avg_grade,
            ROUND(sp.completion_rate, 4) AS completion_rate,
            ROUND(COALESCE(le.engagement_score, 0), 2) AS engagement_score,
            sp.risk_flag
        FROM student_performance_gold sp
        LEFT JOIN lms_engagement_gold le ON sp.student_id = le.student_id
        WHERE 1=1
    """
    if faculty:
        sql += f" AND sp.faculty = '{faculty}'"
    if group_id:
        sql += f" AND sp.group_id = '{group_id}'"
    sql += " ORDER BY sp.full_name"
    return run_query(sql)


def get_room_utilization() -> pd.DataFrame:
    """Return room utilization metrics."""
    return run_query(
        """
        SELECT
            building_id,
            room_id,
            capacity,
            entered_events,
            left_events,
            estimated_current_people,
            ROUND(utilization_rate, 4) AS utilization_rate
        FROM room_utilization_gold
        ORDER BY utilization_rate DESC
        """
    )


def get_lms_engagement() -> pd.DataFrame:
    """Return LMS engagement metrics by student."""
    return run_query(
        """
        SELECT
            student_id,
            total_lms_events,
            login_count,
            course_view_count,
            material_download_count,
            forum_post_count,
            total_duration_minutes,
            ROUND(engagement_score, 2) AS engagement_score
        FROM lms_engagement_gold
        ORDER BY engagement_score DESC
        """
    )
