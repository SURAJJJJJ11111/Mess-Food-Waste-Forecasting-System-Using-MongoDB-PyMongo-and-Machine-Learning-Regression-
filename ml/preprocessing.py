"""
Data Preprocessing Pipeline Module
Extracts operational features available strictly prior to cooking time,
constructs time-aware train/test splits to avoid temporal leakage,
and builds reproducible scikit-learn transformers.
"""

import sys
from pathlib import Path
from typing import Tuple, Dict, Any, List

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
import config

NUMERICAL_FEATURES = [
    "expected_attendance",
    "total_prepared_kg",
    "prev_leftover_kg",
    "prev_attendance",
    "planned_per_capita",
    "is_weekend",
    "special_event_int"
]

CATEGORICAL_FEATURES = [
    "meal_type",
    "day_of_week",
    "weather_condition"
]

TARGET_COLUMN = "total_leftover_kg"
HIGH_WASTE_THRESHOLD_KG = 35.0  # Defined threshold for binary high-waste classification


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms raw operational records into pre-meal predictive features.
    Strictly avoids post-meal leakage columns (actual_attendance, total_served_kg, total_waste_kg).
    """
    data = df.copy()

    # Temporal day category
    if "is_weekend" not in data.columns:
        data["is_weekend"] = data["day_of_week"].apply(lambda d: 1 if d in ["Saturday", "Sunday"] else 0)

    # Boolean event to integer
    data["special_event_int"] = data["special_event"].apply(lambda x: 1 if str(x).lower() in ["true", "1"] else 0)

    # Chef's planned portion per expected diner
    data["planned_per_capita"] = (
        data["total_prepared_kg"] / data["expected_attendance"].replace(0, 1)
    ).round(4)

    # Fill rolling lag nulls if any with training medians
    if "prev_leftover_kg" not in data.columns:
        data["prev_leftover_kg"] = 25.0
    else:
        data["prev_leftover_kg"] = data["prev_leftover_kg"].fillna(25.0)

    if "prev_attendance" not in data.columns:
        data["prev_attendance"] = 650
    else:
        data["prev_attendance"] = data["prev_attendance"].fillna(650)

    # Create classification target if actual leftover exists
    if TARGET_COLUMN in data.columns:
        data["is_high_waste"] = (data[TARGET_COLUMN] > HIGH_WASTE_THRESHOLD_KG).astype(int)

    return data


def create_preprocessor() -> ColumnTransformer:
    """Creates a ColumnTransformer with OneHotEncoder and StandardScaler."""
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERICAL_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES)
        ],
        remainder="drop"
    )


def time_aware_train_test_split(
    df: pd.DataFrame,
    test_ratio: float = 0.20
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits records chronologically: older 80% for training, newest 20% for testing.
    Prevents temporal data leakage and realistically mimics live operations.
    """
    sorted_df = df.sort_values(by=["meal_date", "meal_type"]).reset_index(drop=True)
    split_index = int(len(sorted_df) * (1.0 - test_ratio))

    train_df = sorted_df.iloc[:split_index].copy()
    test_df = sorted_df.iloc[split_index:].copy()

    return train_df, test_df
