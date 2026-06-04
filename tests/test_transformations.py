"""Tests for silver layer transformations."""

import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import SILVER_DIR


@pytest.fixture(scope="module")
def silver_grades():
    """Load silver grades table, skip if pipeline not run."""
    path = SILVER_DIR / "grades.parquet"
    if not path.exists():
        pytest.skip("Silver layer not built. Run run_pipeline.py first.")
    return pd.read_parquet(path)


def test_silver_no_grades_out_of_range(silver_grades):
    """Silver grades should only contain values between 0 and 100."""
    out_of_range = silver_grades[
        (silver_grades["grade"] < 0) | (silver_grades["grade"] > 100)
    ]
    assert len(out_of_range) == 0


def test_silver_no_duplicate_grade_ids(silver_grades):
    """Silver grades should have unique grade_id values."""
    duplicates = silver_grades["grade_id"].duplicated().sum()
    assert duplicates == 0
