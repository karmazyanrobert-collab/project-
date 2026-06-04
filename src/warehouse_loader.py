"""DuckDB analytical warehouse loader."""

import duckdb
import pandas as pd

from src.config import FEATURES_DIR, GOLD_DIR, WAREHOUSE_PATH
from src.utils import print_step, read_parquet


def _get_connection() -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection to the warehouse database."""
    WAREHOUSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(WAREHOUSE_PATH))


def load_gold_to_warehouse() -> dict[str, int]:
    """Load gold tables and feature store into DuckDB warehouse."""
    print_step("DuckDB Warehouse: Loading tables")

    tables = {
        "student_performance_gold": GOLD_DIR / "student_performance_gold.parquet",
        "faculty_performance_gold": GOLD_DIR / "faculty_performance_gold.parquet",
        "lms_engagement_gold": GOLD_DIR / "lms_engagement_gold.parquet",
        "room_utilization_gold": GOLD_DIR / "room_utilization_gold.parquet",
        "student_features": FEATURES_DIR / "student_features.parquet",
    }

    counts: dict[str, int] = {}
    con = _get_connection()

    try:
        for table_name, parquet_path in tables.items():
            df = read_parquet(parquet_path)
            con.execute(f"DROP TABLE IF EXISTS {table_name}")
            con.register("_tmp_df", df)
            con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM _tmp_df")
            con.unregister("_tmp_df")
            counts[table_name] = len(df)
            print(f"  Loaded {table_name}: {len(df)} rows")
    finally:
        con.close()

    print(f"  Warehouse saved to {WAREHOUSE_PATH}")
    return counts


def run_query(sql: str) -> pd.DataFrame:
    """Execute a SQL query against the DuckDB warehouse and return results."""
    con = _get_connection()
    try:
        return con.execute(sql).fetchdf()
    finally:
        con.close()
