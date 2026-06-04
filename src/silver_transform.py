"""Silver layer transformations: cleaned and validated data."""

import pandas as pd

from src.config import BRONZE_DIR, SILVER_DIR
from src.utils import print_step, read_parquet, write_parquet


def _clean_students(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Clean student records."""
    before = len(df)
    cleaned = df.dropna(subset=["student_id", "full_name"]).copy()
    cleaned = cleaned.drop_duplicates(subset=["student_id"], keep="first")
    cleaned["enrollment_year"] = pd.to_numeric(
        cleaned["enrollment_year"], errors="coerce"
    ).astype("Int64")
    return cleaned, before - len(cleaned)


def _clean_grades(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Clean grade records."""
    before = len(df)
    cleaned = df.dropna(subset=["student_id", "course_id"]).copy()
    cleaned = cleaned.drop_duplicates(subset=["grade_id"], keep="first")
    cleaned["grade"] = pd.to_numeric(cleaned["grade"], errors="coerce")
    cleaned = cleaned[(cleaned["grade"] >= 0) & (cleaned["grade"] <= 100)]
    cleaned["grade"] = cleaned["grade"].astype(float)
    return cleaned, before - len(cleaned)


def _clean_assignments(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Clean assignment records."""
    before = len(df)
    cleaned = df.drop_duplicates(subset=["assignment_id"], keep="first").copy()
    cleaned["submitted"] = cleaned["submitted"].map(
        {
            True: True,
            False: False,
            "True": True,
            "False": False,
            "true": True,
            "false": False,
            1: True,
            0: False,
        }
    )
    cleaned["score"] = pd.to_numeric(cleaned["score"], errors="coerce")
    score_mask = cleaned["score"].isna() | (
        (cleaned["score"] >= 0) & (cleaned["score"] <= 100)
    )
    cleaned = cleaned[score_mask]
    return cleaned, before - len(cleaned)


def _clean_lms_activity(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Clean LMS activity records."""
    before = len(df)
    cleaned = df.drop_duplicates(subset=["activity_id"], keep="first").copy()
    cleaned["duration_minutes"] = pd.to_numeric(
        cleaned["duration_minutes"], errors="coerce"
    )
    cleaned = cleaned[
        (cleaned["duration_minutes"] >= 1) & (cleaned["duration_minutes"] <= 180)
    ]
    return cleaned, before - len(cleaned)


def _clean_rooms(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Clean room inventory records."""
    before = len(df)
    cleaned = df.drop_duplicates(subset=["room_id"], keep="first").copy()
    cleaned["capacity"] = pd.to_numeric(cleaned["capacity"], errors="coerce")
    cleaned = cleaned[cleaned["capacity"] > 0]
    return cleaned, before - len(cleaned)


def _clean_room_events(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Clean room event records."""
    before = len(df)
    cleaned = df.drop_duplicates(subset=["event_id"], keep="first").copy()
    cleaned = cleaned[cleaned["event_type"].isin(["entered_room", "left_room"])]
    return cleaned, before - len(cleaned)


CLEANERS = {
    "students": _clean_students,
    "grades": _clean_grades,
    "assignments": _clean_assignments,
    "lms_activity": _clean_lms_activity,
    "rooms": _clean_rooms,
    "room_events": _clean_room_events,
}


def transform_bronze_to_silver() -> dict[str, dict[str, int]]:
    """Transform bronze Parquet files into cleaned silver layer."""
    print_step("Silver Layer: Cleaning bronze data")

    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    stats: dict[str, dict[str, int]] = {}

    for table_name, cleaner in CLEANERS.items():
        bronze_path = BRONZE_DIR / f"{table_name}.parquet"
        if not bronze_path.exists():
            print(f"  Skipping {table_name}: bronze file not found")
            continue

        df = read_parquet(bronze_path)
        before_count = len(df)
        cleaned_df, removed = cleaner(df)
        after_count = len(cleaned_df)

        silver_path = SILVER_DIR / f"{table_name}.parquet"
        write_parquet(cleaned_df, silver_path)

        stats[table_name] = {
            "before": before_count,
            "after": after_count,
            "removed": removed,
        }
        print(
            f"  {table_name}: {before_count} -> {after_count} "
            f"(removed {removed} rows)"
        )

    # Pass through courses unchanged
    courses_path = BRONZE_DIR / "courses.parquet"
    if courses_path.exists():
        courses_df = read_parquet(courses_path)
        write_parquet(courses_df, SILVER_DIR / "courses.parquet")
        print(f"  courses: {len(courses_df)} rows (passed through)")

    return stats
