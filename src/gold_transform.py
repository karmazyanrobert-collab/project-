"""Gold layer transformations: business-ready analytical tables."""

import pandas as pd

from src.config import GOLD_DIR, SILVER_DIR
from src.utils import print_step, read_parquet, write_parquet


def _build_student_performance(
    students: pd.DataFrame,
    grades: pd.DataFrame,
    assignments: pd.DataFrame,
) -> pd.DataFrame:
    """Build student performance gold table with risk flags."""
    grade_agg = (
        grades.groupby("student_id")
        .agg(
            avg_grade=("grade", "mean"),
            min_grade=("grade", "min"),
            max_grade=("grade", "max"),
            courses_count=("course_id", "nunique"),
        )
        .reset_index()
    )

    assign_agg = (
        assignments.groupby("student_id")
        .agg(
            assignments_total=("assignment_id", "count"),
            assignments_submitted=("submitted", lambda s: int(s.sum())),
            avg_assignment_score=("score", "mean"),
        )
        .reset_index()
    )
    assign_agg["completion_rate"] = (
        assign_agg["assignments_submitted"] / assign_agg["assignments_total"]
    ).fillna(0)

    result = students.merge(grade_agg, on="student_id", how="left")
    result = result.merge(assign_agg, on="student_id", how="left")

    for col in ["avg_grade", "min_grade", "max_grade", "courses_count",
                "assignments_total", "assignments_submitted",
                "completion_rate", "avg_assignment_score"]:
        if col in result.columns:
            result[col] = result[col].fillna(0)

    result["risk_flag"] = (
        (result["avg_grade"] < 60) | (result["completion_rate"] < 0.6)
    ).astype(int)

    return result[
        [
            "student_id",
            "full_name",
            "faculty",
            "group_id",
            "avg_grade",
            "min_grade",
            "max_grade",
            "courses_count",
            "assignments_total",
            "assignments_submitted",
            "completion_rate",
            "avg_assignment_score",
            "risk_flag",
        ]
    ]


def _build_faculty_performance(student_perf: pd.DataFrame) -> pd.DataFrame:
    """Build faculty-level performance aggregates."""
    faculty_agg = (
        student_perf.groupby("faculty")
        .agg(
            students_count=("student_id", "count"),
            avg_grade=("avg_grade", "mean"),
            avg_completion_rate=("completion_rate", "mean"),
            risk_students_count=("risk_flag", "sum"),
        )
        .reset_index()
    )
    faculty_agg["risk_students_share"] = (
        faculty_agg["risk_students_count"] / faculty_agg["students_count"]
    )
    return faculty_agg


def _build_lms_engagement(lms_activity: pd.DataFrame) -> pd.DataFrame:
    """Build LMS engagement gold table with engagement score."""
    engagement = (
        lms_activity.groupby("student_id")
        .agg(
            total_lms_events=("activity_id", "count"),
            login_count=("activity_type", lambda s: (s == "login").sum()),
            course_view_count=("activity_type", lambda s: (s == "course_view").sum()),
            material_download_count=(
                "activity_type", lambda s: (s == "material_download").sum()
            ),
            forum_post_count=("activity_type", lambda s: (s == "forum_post").sum()),
            total_duration_minutes=("duration_minutes", "sum"),
        )
        .reset_index()
    )

    max_events = engagement["total_lms_events"].max() or 1
    max_duration = engagement["total_duration_minutes"].max() or 1

    engagement["engagement_score"] = (
        engagement["total_lms_events"] / max_events * 0.5
        + engagement["total_duration_minutes"] / max_duration * 0.5
    ) * 100

    return engagement


def _build_room_utilization(
    rooms: pd.DataFrame, room_events: pd.DataFrame
) -> pd.DataFrame:
    """Build room utilization gold table."""
    entered = (
        room_events[room_events["event_type"] == "entered_room"]
        .groupby(["building_id", "room_id"])
        .size()
        .reset_index(name="entered_events")
    )
    left = (
        room_events[room_events["event_type"] == "left_room"]
        .groupby(["building_id", "room_id"])
        .size()
        .reset_index(name="left_events")
    )

    utilization = rooms.merge(
        entered, on=["building_id", "room_id"], how="left"
    ).merge(left, on=["building_id", "room_id"], how="left")

    utilization["entered_events"] = utilization["entered_events"].fillna(0).astype(int)
    utilization["left_events"] = utilization["left_events"].fillna(0).astype(int)
    utilization["estimated_current_people"] = (
        utilization["entered_events"] - utilization["left_events"]
    ).clip(lower=0)
    utilization["utilization_rate"] = (
        utilization["estimated_current_people"] / utilization["capacity"]
    ).clip(upper=1.0)

    return utilization[
        [
            "building_id",
            "room_id",
            "capacity",
            "entered_events",
            "left_events",
            "estimated_current_people",
            "utilization_rate",
        ]
    ]


def transform_silver_to_gold() -> dict[str, int]:
    """Transform silver layer data into gold analytical tables."""
    print_step("Gold Layer: Building analytical tables")

    students = read_parquet(SILVER_DIR / "students.parquet")
    grades = read_parquet(SILVER_DIR / "grades.parquet")
    assignments = read_parquet(SILVER_DIR / "assignments.parquet")
    lms_activity = read_parquet(SILVER_DIR / "lms_activity.parquet")
    rooms = read_parquet(SILVER_DIR / "rooms.parquet")
    room_events = read_parquet(SILVER_DIR / "room_events.parquet")

    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    gold_tables = {
        "student_performance_gold.parquet": _build_student_performance(
            students, grades, assignments
        ),
        "faculty_performance_gold.parquet": None,
        "lms_engagement_gold.parquet": _build_lms_engagement(lms_activity),
        "room_utilization_gold.parquet": _build_room_utilization(rooms, room_events),
    }

    student_perf = gold_tables["student_performance_gold.parquet"]
    gold_tables["faculty_performance_gold.parquet"] = _build_faculty_performance(
        student_perf
    )

    counts: dict[str, int] = {}
    for filename, df in gold_tables.items():
        if df is not None:
            path = GOLD_DIR / filename
            write_parquet(df, path)
            counts[filename] = len(df)
            print(f"  {filename}: {len(df)} rows")

    return counts
