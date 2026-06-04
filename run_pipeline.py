"""Main ETL/ELT pipeline orchestrator."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.bronze_loader import load_to_bronze
from src.config import ensure_directories
from src.data_quality import run_data_quality_checks
from src.feature_store import build_feature_store
from src.generate_data import generate_source_data
from src.gold_transform import transform_silver_to_gold
from src.silver_transform import transform_bronze_to_silver
from src.utils import print_step
from src.warehouse_loader import load_gold_to_warehouse


def main() -> None:
    """Run the full data pipeline from source generation to warehouse load."""
    print("\n" + "=" * 60)
    print("  University Data Platform — Pipeline")
    print("=" * 60)

    print_step("Step 1: Creating directories")
    ensure_directories()
    print("  Directories ready.")

    print_step("Step 2: Generating source data")
    generate_source_data()

    print_step("Step 3: Loading to Bronze layer")
    load_to_bronze()

    print_step("Step 4: Data Quality checks (Bronze)")
    run_data_quality_checks("bronze")

    print_step("Step 5: Transforming Bronze to Silver")
    transform_bronze_to_silver()

    print_step("Step 6: Data Quality checks (Silver)")
    run_data_quality_checks("silver")

    print_step("Step 7: Transforming Silver to Gold")
    transform_silver_to_gold()

    print_step("Step 8: Building Feature Store")
    build_feature_store()

    print_step("Step 9: Loading to DuckDB Warehouse")
    load_gold_to_warehouse()

    print("\n" + "=" * 60)
    print("  Pipeline completed successfully.")
    print("  Open dashboard with:")
    print("    streamlit run dashboard/app.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
