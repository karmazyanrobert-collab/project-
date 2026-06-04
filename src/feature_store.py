"""Local Feature Store backed by Parquet files."""

import pandas as pd

from src.config import FEATURES_DIR, GOLD_DIR
from src.utils import print_step, read_parquet, write_parquet

FEATURE_COLUMNS = [
    "student_id",
    "avg_grade",
    "completion_rate",
    "avg_assignment_score",
    "total_lms_events",
    "total_duration_minutes",
    "engagement_score",
    "risk_flag",
]


def build_feature_store() -> pd.DataFrame:
    """Build student feature table from gold layer tables."""
    print_step("Feature Store: Building student features")

    student_perf = read_parquet(GOLD_DIR / "student_performance_gold.parquet")
    lms_engagement = read_parquet(GOLD_DIR / "lms_engagement_gold.parquet")

    features = student_perf.merge(
        lms_engagement[
            [
                "student_id",
                "total_lms_events",
                "total_duration_minutes",
                "engagement_score",
            ]
        ],
        on="student_id",
        how="left",
    )

    for col in ["total_lms_events", "total_duration_minutes", "engagement_score"]:
        features[col] = features[col].fillna(0)

    features = features[FEATURE_COLUMNS].copy()

    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    feature_path = FEATURES_DIR / "student_features.parquet"
    write_parquet(features, feature_path)
    print(f"  student_features.parquet: {len(features)} rows")
    print(f"  Saved to {feature_path}")

    return features


def get_features_for_students(student_ids: list) -> pd.DataFrame:
    """Return feature rows for the given student IDs."""
    feature_path = FEATURES_DIR / "student_features.parquet"
    if not feature_path.exists():
        raise FileNotFoundError(
            "Feature store not built. Run build_feature_store() first."
        )

    features = read_parquet(feature_path)
    return features[features["student_id"].isin(student_ids)].reset_index(drop=True)
