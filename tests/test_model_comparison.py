"""
Automated Unit and Integration Tests for Model Comparison
Validates:
1. Both RandomForestRegressor and DecisionTreeRegressor can be trained and saved.
2. Both models produce valid numerical predictions on identical test inputs.
3. Both models are evaluated on the exact same test records.
4. MAE, RMSE, and R² are calculated correctly without NaN.
5. Saved models can be loaded from disk.
6. Preprocessing and feature ordering are consistent.
7. Model comparison JSON/CSV reports contain both models and required metrics.
"""

import sys
import json
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import joblib

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from ml.preprocessing import (
    engineer_features,
    create_preprocessor,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET_COLUMN
)
from ml.predict import predict_meal_leftovers, get_trained_models
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score


@pytest.fixture
def sample_dataset():
    """Generates synthetic pre-meal records for self-contained regression tests."""
    np.random.seed(42)
    n = 100
    dates = pd.date_range("2026-01-01", periods=n, freq="D").strftime("%Y-%m-%d")
    meal_types = np.random.choice(["Breakfast", "Lunch", "Snacks", "Dinner"], size=n)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_names = [days[i % 7] for i in range(n)]
    attendance = np.random.randint(400, 1000, size=n)
    prepared = (attendance * np.random.uniform(0.35, 0.55, size=n)).round(1)
    leftovers = np.clip((prepared * np.random.uniform(0.04, 0.16, size=n)).round(1), 0.0, None)

    df = pd.DataFrame({
        "meal_date": dates,
        "meal_type": meal_types,
        "day_of_week": day_names,
        "expected_attendance": attendance,
        "total_prepared_kg": prepared,
        "total_leftover_kg": leftovers,
        "weather_condition": np.random.choice(["Sunny", "Rainy", "Pleasant", "Cold"], size=n),
        "special_event": np.random.choice([False, True], size=n, p=[0.85, 0.15]),
        "prev_leftover_kg": np.random.uniform(10, 40, size=n).round(1),
        "prev_attendance": np.random.randint(400, 1000, size=n)
    })
    return df


def test_saved_models_exist_and_loadable():
    """Verifies that both trained models exist on disk and can be unpickled."""
    assert config.RF_MODEL_PATH.exists(), f"Random Forest model missing at {config.RF_MODEL_PATH}"
    assert config.DT_MODEL_PATH.exists(), f"Decision Tree model missing at {config.DT_MODEL_PATH}"

    rf_model = joblib.load(config.RF_MODEL_PATH)
    dt_model = joblib.load(config.DT_MODEL_PATH)

    assert hasattr(rf_model, "predict"), "RF model must have predict method"
    assert hasattr(dt_model, "predict"), "DT model must have predict method"


def test_both_regressors_train_and_predict(sample_dataset):
    """Verifies that both regressors can be trained on identical data and predict values."""
    featured = engineer_features(sample_dataset)
    feature_cols = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
    X = featured[feature_cols]
    y = featured[TARGET_COLUMN]

    # Split
    X_tr, X_te = X.iloc[:80], X.iloc[80:]
    y_tr, y_te = y.iloc[:80], y.iloc[80:]

    # Train RF
    rf_pipe = Pipeline([
        ("prep", create_preprocessor()),
        ("reg", RandomForestRegressor(n_estimators=10, max_depth=5, random_state=42))
    ])
    rf_pipe.fit(X_tr, y_tr)
    y_rf = rf_pipe.predict(X_te)

    # Train DT
    dt_pipe = Pipeline([
        ("prep", create_preprocessor()),
        ("reg", DecisionTreeRegressor(max_depth=5, random_state=42))
    ])
    dt_pipe.fit(X_tr, y_tr)
    y_dt = dt_pipe.predict(X_te)

    # Numerical predictions check
    assert len(y_rf) == len(X_te)
    assert len(y_dt) == len(X_te)
    assert not np.isnan(y_rf).any(), "RF predictions must not contain NaN"
    assert not np.isnan(y_dt).any(), "DT predictions must not contain NaN"


def test_fair_evaluation_metrics_identical_test_set(sample_dataset):
    """Verifies that both regressors are evaluated on the exact same test records."""
    featured = engineer_features(sample_dataset)
    feature_cols = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
    X_train, X_test = featured[feature_cols].iloc[:80], featured[feature_cols].iloc[80:]
    y_train, y_test = featured[TARGET_COLUMN].iloc[:80], featured[TARGET_COLUMN].iloc[80:]

    rf = Pipeline([("prep", create_preprocessor()), ("reg", RandomForestRegressor(n_estimators=10, random_state=42))])
    dt = Pipeline([("prep", create_preprocessor()), ("reg", DecisionTreeRegressor(random_state=42))])

    rf.fit(X_train, y_train)
    dt.fit(X_train, y_train)

    pred_rf = np.clip(rf.predict(X_test), 0.0, None)
    pred_dt = np.clip(dt.predict(X_test), 0.0, None)

    # Calculate metrics
    mae_rf = mean_absolute_error(y_test, pred_rf)
    rmse_rf = root_mean_squared_error(y_test, pred_rf)
    r2_rf = r2_score(y_test, pred_rf)

    mae_dt = mean_absolute_error(y_test, pred_dt)
    rmse_dt = root_mean_squared_error(y_test, pred_dt)
    r2_dt = r2_score(y_test, pred_dt)

    assert mae_rf >= 0.0
    assert mae_dt >= 0.0
    assert rmse_rf >= 0.0
    assert rmse_dt >= 0.0
    assert not np.isnan(r2_rf)
    assert not np.isnan(r2_dt)


def test_feature_ordering_and_preprocessor_consistency():
    """Verifies that feature columns and preprocessing pipelines are identical across models."""
    rf_pipeline, _, rf_name = get_trained_models("random_forest")
    dt_pipeline, _, dt_name = get_trained_models("decision_tree")

    assert rf_name == "RandomForestRegressor"
    assert dt_name == "DecisionTreeRegressor"

    rf_prep = rf_pipeline.named_steps["preprocessor"]
    dt_prep = dt_pipeline.named_steps["preprocessor"]

    assert len(rf_prep.transformers) == len(dt_prep.transformers)
    rf_cols = rf_prep.transformers[0][2] + rf_prep.transformers[1][2]
    dt_cols = dt_prep.transformers[0][2] + dt_prep.transformers[1][2]
    assert rf_cols == dt_cols, "Feature list and ordering must be identical between RF and DT"


def test_model_comparison_report_structure():
    """Verifies that report/model_comparison.json exists and contains both models with metrics."""
    assert config.MODEL_COMPARISON_JSON_PATH.exists(), f"Comparison JSON missing at {config.MODEL_COMPARISON_JSON_PATH}"

    with open(config.MODEL_COMPARISON_JSON_PATH, "r", encoding="utf-8") as f:
        comp_data = json.load(f)

    assert "models_evaluated" in comp_data
    models = comp_data["models_evaluated"]
    model_names = [m["model_name"] for m in models]

    assert "Random Forest Regressor" in model_names
    assert "Decision Tree Regressor" in model_names

    for m in models:
        assert "mae_kg" in m
        assert "rmse_kg" in m
        assert "r2_score" in m
        assert m["mae_kg"] > 0
        assert m["rmse_kg"] > 0
