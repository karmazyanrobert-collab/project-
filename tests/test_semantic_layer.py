"""Tests for semantic layer."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import WAREHOUSE_PATH
from src.semantic_layer import get_faculty_metrics, get_kpi_summary


@pytest.fixture(scope="module")
def require_warehouse():
    """Skip tests if warehouse has not been built."""
    if not WAREHOUSE_PATH.exists():
        pytest.skip("Warehouse not built. Run run_pipeline.py first.")


def test_kpi_summary_not_empty(require_warehouse):
    """KPI summary should return populated metrics."""
    kpi = get_kpi_summary()
    assert kpi
    assert kpi["total_students"] > 0
    assert "avg_grade" in kpi
    assert "risk_students" in kpi


def test_faculty_metrics_returns_faculties(require_warehouse):
    """Faculty metrics should return multiple faculties."""
    df = get_faculty_metrics()
    assert not df.empty
    assert "faculty" in df.columns
    assert len(df) >= 3
