"""Simple pandas-based data quality framework."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.config import BRONZE_DIR, LOGS_DIR, SILVER_DIR
from src.utils import read_parquet


@dataclass
class DataQualityReport:
    """Single data quality check result."""

    check_name: str
    table_name: str
    status: str
    failed_count: int
    message: str

    def to_dict(self) -> dict:
        """Convert report entry to dictionary."""
        return {
            "check_name": self.check_name,
            "table_name": self.table_name,
            "status": self.status,
            "failed_count": self.failed_count,
            "message": self.message,
        }


def _check_not_null(df: pd.DataFrame, column: str, table_name: str) -> DataQualityReport:
    """Verify column has no null values."""
    failed = int(df[column].isna().sum())
    return DataQualityReport(
        check_name=f"{column}_not_null",
        table_name=table_name,
        status="PASSED" if failed == 0 else "FAILED",
        failed_count=failed,
        message=f"{failed} null values in {column}",
    )


def _check_unique(df: pd.DataFrame, column: str, table_name: str) -> DataQualityReport:
    """Verify column values are unique."""
    failed = int(df[column].duplicated(keep=False).sum())
    return DataQualityReport(
        check_name=f"{column}_unique",
        table_name=table_name,
        status="PASSED" if failed == 0 else "FAILED",
        failed_count=failed,
        message=f"{failed} duplicate values in {column}",
    )


def _check_between(
    df: pd.DataFrame, column: str, low: float, high: float, table_name: str
) -> DataQualityReport:
    """Verify numeric column is within inclusive range."""
    numeric = pd.to_numeric(df[column], errors="coerce")
    mask = numeric.notna() & ((numeric < low) | (numeric > high))
    failed = int(mask.sum())
    return DataQualityReport(
        check_name=f"{column}_between_{low}_and_{high}",
        table_name=table_name,
        status="PASSED" if failed == 0 else "FAILED",
        failed_count=failed,
        message=f"{failed} values outside [{low}, {high}] in {column}",
    )


def _check_in_values(
    df: pd.DataFrame, column: str, allowed: list, table_name: str
) -> DataQualityReport:
    """Verify column values belong to allowed set."""
    failed = int((~df[column].isin(allowed)).sum())
    return DataQualityReport(
        check_name=f"{column}_in_allowed_values",
        table_name=table_name,
        status="PASSED" if failed == 0 else "FAILED",
        failed_count=failed,
        message=f"{failed} invalid values in {column}",
    )


def _check_boolean(df: pd.DataFrame, column: str, table_name: str) -> DataQualityReport:
    """Verify column contains boolean-compatible values."""
    valid = df[column].isin([True, False, "True", "False", "true", "false", 1, 0])
    failed = int((~valid & df[column].notna()).sum())
    return DataQualityReport(
        check_name=f"{column}_is_boolean",
        table_name=table_name,
        status="PASSED" if failed == 0 else "FAILED",
        failed_count=failed,
        message=f"{failed} non-boolean values in {column}",
    )


def _check_greater_than(
    df: pd.DataFrame, column: str, threshold: float, table_name: str
) -> DataQualityReport:
    """Verify numeric column values are greater than threshold."""
    numeric = pd.to_numeric(df[column], errors="coerce")
    failed = int((numeric <= threshold).sum())
    return DataQualityReport(
        check_name=f"{column}_greater_than_{threshold}",
        table_name=table_name,
        status="PASSED" if failed == 0 else "FAILED",
        failed_count=failed,
        message=f"{failed} values <= {threshold} in {column}",
    )


TABLE_CHECKS = {
    "students": lambda df: [
        _check_not_null(df, "student_id", "students"),
        _check_not_null(df, "full_name", "students"),
        _check_unique(df, "student_id", "students"),
    ],
    "grades": lambda df: [
        _check_unique(df, "grade_id", "grades"),
        _check_not_null(df, "student_id", "grades"),
        _check_not_null(df, "course_id", "grades"),
        _check_between(df, "grade", 0, 100, "grades"),
    ],
    "assignments": lambda df: [
        _check_unique(df, "assignment_id", "assignments"),
        _check_not_null(df, "student_id", "assignments"),
        _check_between(df, "score", 0, 100, "assignments"),
        _check_boolean(df, "submitted", "assignments"),
    ],
    "lms_activity": lambda df: [
        _check_unique(df, "activity_id", "lms_activity"),
        _check_not_null(df, "student_id", "lms_activity"),
        _check_between(df, "duration_minutes", 1, 180, "lms_activity"),
    ],
    "rooms": lambda df: [
        _check_unique(df, "room_id", "rooms"),
        _check_greater_than(df, "capacity", 0, "rooms"),
    ],
    "room_events": lambda df: [
        _check_unique(df, "event_id", "room_events"),
        _check_not_null(df, "student_id", "room_events"),
        _check_in_values(df, "event_type", ["entered_room", "left_room"], "room_events"),
    ],
}


def _layer_dir(layer: str) -> Path:
    """Return directory path for the given data layer."""
    if layer == "bronze":
        return BRONZE_DIR
    if layer == "silver":
        return SILVER_DIR
    raise ValueError(f"Unsupported layer: {layer}")


def run_data_quality_checks(layer: str = "bronze") -> pd.DataFrame:
    """Run data quality checks on Parquet files in the specified layer."""
    layer_dir = _layer_dir(layer)
    reports: list[DataQualityReport] = []

    for table_name, check_fn in TABLE_CHECKS.items():
        parquet_path = layer_dir / f"{table_name}.parquet"
        if not parquet_path.exists():
            print(f"  Skipping {table_name}: file not found in {layer}")
            continue

        df = read_parquet(parquet_path)
        table_reports = check_fn(df)
        reports.extend(table_reports)

        for report in table_reports:
            status_icon = "OK" if report.status == "PASSED" else "FAIL"
            print(
                f"  [{status_icon}] {report.table_name}.{report.check_name}: "
                f"{report.status} ({report.message})"
            )

    report_df = pd.DataFrame([r.to_dict() for r in reports])
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = LOGS_DIR / "data_quality_report.csv"
    report_df.to_csv(report_path, index=False)

    passed = int((report_df["status"] == "PASSED").sum()) if not report_df.empty else 0
    failed = int((report_df["status"] == "FAILED").sum()) if not report_df.empty else 0
    print(f"\n  Data Quality Summary ({layer}): {passed} passed, {failed} failed")
    print(f"  Report saved to {report_path}")

    return report_df
