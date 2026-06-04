"""Bronze layer loader: raw CSV to Parquet."""

from pathlib import Path

import pandas as pd

from src.config import BRONZE_DIR, SOURCE_DIR
from src.utils import print_step, write_parquet


def load_to_bronze() -> dict[str, int]:
    """Load all source CSV files into the bronze Parquet layer without cleaning."""
    print_step("Bronze Layer: Loading source CSV to Parquet")

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    csv_files = sorted(SOURCE_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {SOURCE_DIR}")

    for csv_path in csv_files:
        df = pd.read_csv(csv_path)
        parquet_name = csv_path.stem + ".parquet"
        parquet_path = BRONZE_DIR / parquet_name
        write_parquet(df, parquet_path)
        counts[parquet_name] = len(df)
        print(f"  {csv_path.name} -> {parquet_name}: {len(df)} rows")

    return counts
