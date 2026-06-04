"""Test runner script."""

import subprocess
import sys
from pathlib import Path

from src.config import SILVER_DIR, WAREHOUSE_PATH


def main() -> int:
    """Run pytest with verbose output."""
    project_root = Path(__file__).resolve().parent
    if not WAREHOUSE_PATH.exists() or not (SILVER_DIR / "grades.parquet").exists():
        print(
            "Warehouse or Silver data not found. Running pipeline before tests...",
            flush=True,
        )
        from run_pipeline import main as run_pipeline_main

        run_pipeline_main()
        sys.stdout.flush()

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-v"],
        cwd=str(project_root),
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
