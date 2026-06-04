"""Tests for data quality framework."""

import pandas as pd

from src.data_quality import DataQualityReport, _check_between


def test_data_quality_report_creation():
    """DataQualityReport should store all fields correctly."""
    report = DataQualityReport(
        check_name="grade_between_0_and_100",
        table_name="grades",
        status="FAILED",
        failed_count=3,
        message="3 values outside [0, 100] in grade",
    )
    result = report.to_dict()
    assert result["check_name"] == "grade_between_0_and_100"
    assert result["table_name"] == "grades"
    assert result["status"] == "FAILED"
    assert result["failed_count"] == 3


def test_grade_range_check_catches_errors():
    """Grade range check should detect out-of-range values."""
    df = pd.DataFrame({"grade": [50, 75, -5, 120, 90]})
    report = _check_between(df, "grade", 0, 100, "grades")
    assert report.status == "FAILED"
    assert report.failed_count == 2
