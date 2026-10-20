"""
Model Training Script for Mess Food Waste Forecasting
Trains Random Forest Regressor and High-Waste Classifier pipelines,
evaluates on unseen chronologically held-out test data,
benchmarks against meal-type historical baseline, and serializes artifacts.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import (
    mean_absolute_error,
    root_mean_squared_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)

from database.connection import get_db, check_connection
from ml.preprocessing import (
    engineer_features,
    create_preprocessor,
    time_aware_train_test_split,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET_COLUMN,
    HIGH_WASTE_THRESHOLD_KG
)
import config


def load_dataset_from_mongodb() -> pd.DataFrame:
    """Retrieves operational meal records from MongoDB."""
    ok, conn_info = check_connection()
    if not ok:
        raise ConnectionError(f"Cannot load records from MongoDB: {conn_info}")

    db = get_db()
    cursor = db["meal_records"].find(
        {},
        {
            "_id": 0,
            "meal_id": 1,
            "meal_date": 1,
            "meal_type": 1,
            "day_of_week": 1,
            "expected_attendance": 1,
            "total_prepared_kg": 1,
            "total_leftover_kg": 1,
            "weather_condition": 1,
            "special_event": 1
        }
    )
    records = list(cursor)
    if not records:
        raise ValueError("MongoDB collection 'meal_records' is empty. Run seed_database.py first.")

    df = pd.DataFrame(records)
    # Sort chronologically
    df = df.sort_values(by=["meal_date", "meal_type"]).reset_index(drop=True)

    # Compute rolling lag features
    df["prev_leftover_kg"] = df["total_leftover_kg"].shift(1).fillna(20.0)
    # Use expected attendance as lag proxy to avoid post-meal data leakage
    df["prev_attendance"] = df["expected_attendance"].shift(1).fillna(650)

    return df


def train_and_evaluate_models() -> Dict[str, Any]:
    print("=" * 80)
    print("TRAINING REGRESSION & CLASSIFICATION MODELS FOR MESS FOOD WASTE FORECASTING")
    print("Algorithms: Random Forest Regressor vs Decision Tree Regressor")
    print("=" * 80)

    # 1. Load Data
    print("Loading historical meal records from MongoDB...")
    raw_df = load_dataset_from_mongodb()
    print(f"Loaded {len(raw_df)} operational meal records.")

    # 2. Feature Engineering & Chronological Split
    featured_df = engineer_features(raw_df)
    train_df, test_df = time_aware_train_test_split(featured_df, test_ratio=0.20)
    print(f"Chronological Train Set: {len(train_df)} meals ({train_df['meal_date'].min()} to {train_df['meal_date'].max()})")
    print(f"Chronological Test Set:  {len(test_df)} meals ({test_df['meal_date'].min()} to {test_df['meal_date'].max()})")

    feature_cols = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
    X_train = train_df[feature_cols]
    y_train = train_df[TARGET_COLUMN]
    X_test = test_df[feature_cols]
    y_test = test_df[TARGET_COLUMN]

    # -------------------------------------------------------------
    # 3. Baseline Model (Historical Meal-Type Average)
    # -------------------------------------------------------------
    meal_type_means = train_df.groupby("meal_type")[TARGET_COLUMN].mean().to_dict()
    y_pred_baseline = test_df["meal_type"].map(meal_type_means)

    base_mae = float(mean_absolute_error(y_test, y_pred_baseline))
    base_rmse = float(root_mean_squared_error(y_test, y_pred_baseline))
    base_r2 = float(r2_score(y_test, y_pred_baseline))

    # -------------------------------------------------------------
    # 4. Train Random Forest Regressor Pipeline
    # -------------------------------------------------------------
    print("\nTraining Random Forest Regressor pipeline...")
    rf_regressor = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    rf_pipeline = Pipeline([
        ("preprocessor", create_preprocessor()),
        ("regressor", rf_regressor)
    ])
    rf_pipeline.fit(X_train, y_train)

    # Predict and enforce physical non-negative constraint
    y_pred_rf = np.clip(rf_pipeline.predict(X_test), 0.0, None)

    rf_mae = float(mean_absolute_error(y_test, y_pred_rf))
    rf_rmse = float(root_mean_squared_error(y_test, y_pred_rf))
    rf_r2 = float(r2_score(y_test, y_pred_rf))
    rf_mae_improvement_pct = round(((base_mae - rf_mae) / base_mae) * 100, 2)

    # -------------------------------------------------------------
    # 5. Train Decision Tree Regressor Pipeline
    # -------------------------------------------------------------
    print("\nTraining Decision Tree Regressor pipeline...")
    dt_regressor = DecisionTreeRegressor(
        max_depth=6,
        min_samples_split=10,
        min_samples_leaf=8,
        random_state=42
    )
    dt_pipeline = Pipeline([
        ("preprocessor", create_preprocessor()),
        ("regressor", dt_regressor)
    ])
    dt_pipeline.fit(X_train, y_train)

    # Predict and enforce physical non-negative constraint
    y_pred_dt = np.clip(dt_pipeline.predict(X_test), 0.0, None)

    dt_mae = float(mean_absolute_error(y_test, y_pred_dt))
    dt_rmse = float(root_mean_squared_error(y_test, y_pred_dt))
    dt_r2 = float(r2_score(y_test, y_pred_dt))
    dt_mae_improvement_pct = round(((base_mae - dt_mae) / base_mae) * 100, 2)

    # -------------------------------------------------------------
    # 6. Train High-Waste Classification Model
    # -------------------------------------------------------------
    print("\nTraining High-Waste Classification pipeline (Threshold: > 35 kg)...")
    y_train_cls = train_df["is_high_waste"]
    y_test_cls = test_df["is_high_waste"]

    classifier = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        random_state=42,
        n_jobs=-1
    )
    cls_pipeline = Pipeline([
        ("preprocessor", create_preprocessor()),
        ("classifier", classifier)
    ])
    cls_pipeline.fit(X_train, y_train_cls)

    y_pred_cls = cls_pipeline.predict(X_test)
    cls_acc = float(accuracy_score(y_test_cls, y_pred_cls))
    cls_prec = float(precision_score(y_test_cls, y_pred_cls, zero_division=0))
    cls_rec = float(recall_score(y_test_cls, y_pred_cls, zero_division=0))
    cls_f1 = float(f1_score(y_test_cls, y_pred_cls, zero_division=0))

    # -------------------------------------------------------------
    # 7. Extract Feature Importances
    # -------------------------------------------------------------
    ohe_categories = rf_pipeline.named_steps["preprocessor"].named_transformers_["cat"].get_feature_names_out(CATEGORICAL_FEATURES)
    all_feature_names = NUMERICAL_FEATURES + list(ohe_categories)

    rf_importances = rf_pipeline.named_steps["regressor"].feature_importances_
    rf_feat_imp_dict = {
        name: round(float(imp), 4)
        for name, imp in sorted(zip(all_feature_names, rf_importances), key=lambda x: x[1], reverse=True)
    }

    dt_importances = dt_pipeline.named_steps["regressor"].feature_importances_
    dt_feat_imp_dict = {
        name: round(float(imp), 4)
        for name, imp in sorted(zip(all_feature_names, dt_importances), key=lambda x: x[1], reverse=True)
    }

    # -------------------------------------------------------------
    # 8. Serialize Artifacts
    # -------------------------------------------------------------
    joblib.dump(rf_pipeline, config.RF_MODEL_PATH)
    joblib.dump(dt_pipeline, config.DT_MODEL_PATH)
    joblib.dump(cls_pipeline, config.CLASSIFIER_PATH)

    # Determine superior model on test set
    best_model_name = "RandomForestRegressor" if rf_mae <= dt_mae else "DecisionTreeRegressor"
    better_margin = round(abs(rf_mae - dt_mae), 3)

    # Model comparison table structure
    model_comparison_table = [
        {
            "model_name": "Random Forest Regressor",
            "algorithm": "RandomForestRegressor",
            "mae_kg": round(rf_mae, 3),
            "rmse_kg": round(rf_rmse, 3),
            "r2_score": round(rf_r2, 4),
            "mae_improvement_percentage": rf_mae_improvement_pct,
            "status": "Superior Generalization" if rf_mae <= dt_mae else "Alternative Model"
        },
        {
            "model_name": "Decision Tree Regressor",
            "algorithm": "DecisionTreeRegressor",
            "mae_kg": round(dt_mae, 3),
            "rmse_kg": round(dt_rmse, 3),
            "r2_score": round(dt_r2, 4),
            "mae_improvement_percentage": dt_mae_improvement_pct,
            "status": "Superior Generalization" if dt_mae < rf_mae else "Single Tree Baseline"
        },
        {
            "model_name": "Historical Mean Baseline",
            "algorithm": "MealTypeMean",
            "mae_kg": round(base_mae, 3),
            "rmse_kg": round(base_rmse, 3),
            "r2_score": round(base_r2, 4),
            "mae_improvement_percentage": 0.0,
            "status": "Domain Benchmark"
        }
    ]

    metadata = {
        "model_name": "RandomForestRegressor",
        "model_version": "2.0.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "random_seed": 42,
        "n_train_samples": len(train_df),
        "n_test_samples": len(test_df),
        "target_variable": TARGET_COLUMN,
        "features": feature_cols,
        "selected_best_model": best_model_name,
        "model_selection_rationale": (
            f"{best_model_name} demonstrated superior test performance with an MAE of "
            f"{min(rf_mae, dt_mae):.3f} kg (an advantage of {better_margin} kg over the alternative). "
            f"Random Forest ensembles multiple de-correlated trees to damp individual decision tree variance."
        ),
        "model_comparison": model_comparison_table,
        "regression_metrics": {
            "mae_kg": round(rf_mae, 3),
            "rmse_kg": round(rf_rmse, 3),
            "r2_score": round(rf_r2, 4)
        },
        "decision_tree_metrics": {
            "mae_kg": round(dt_mae, 3),
            "rmse_kg": round(dt_rmse, 3),
            "r2_score": round(dt_r2, 4),
            "mae_improvement_percentage": dt_mae_improvement_pct
        },
        "baseline_metrics": {
            "baseline_type": "Historical Mean by Meal Type",
            "mae_kg": round(base_mae, 3),
            "rmse_kg": round(base_rmse, 3),
            "r2_score": round(base_r2, 4),
            "mae_improvement_percentage": rf_mae_improvement_pct
        },
        "classification_metrics": {
            "threshold_kg": HIGH_WASTE_THRESHOLD_KG,
            "accuracy": round(cls_acc, 4),
            "precision": round(cls_prec, 4),
            "recall": round(cls_rec, 4),
            "f1_score": round(cls_f1, 4)
        },
        "feature_importances": rf_feat_imp_dict,
        "dt_feature_importances": dt_feat_imp_dict,
        "hyperparameters": {
            "random_forest": {
                "n_estimators": 100,
                "max_depth": 12,
                "min_samples_split": 4,
                "min_samples_leaf": 2
            },
            "decision_tree": {
                "max_depth": 6,
                "min_samples_split": 10,
                "min_samples_leaf": 8
            }
        }
    }

    with open(config.MODEL_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # -------------------------------------------------------------
    # 9. Export Comparison Results (JSON & CSV)
    # -------------------------------------------------------------
    comparison_export = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_train_samples": len(train_df),
        "n_test_samples": len(test_df),
        "target_variable": TARGET_COLUMN,
        "models_evaluated": model_comparison_table,
        "selected_best_model": best_model_name,
        "high_waste_classifier": {
            "threshold_kg": HIGH_WASTE_THRESHOLD_KG,
            "accuracy": round(cls_acc, 4),
            "precision": round(cls_prec, 4),
            "recall": round(cls_rec, 4),
            "f1_score": round(cls_f1, 4)
        }
    }

    # Save to report/
    config.MODEL_COMPARISON_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(config.MODEL_COMPARISON_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(comparison_export, f, indent=2)

    # Export CSV comparison table
    df_comparison = pd.DataFrame(model_comparison_table)
    config.MODEL_COMPARISON_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_comparison.to_csv(config.MODEL_COMPARISON_CSV_PATH, index=False)

    # Print Formatted Evaluation Report
    print("\n" + "=" * 65)
    print("ALGORITHM COMPARISON RESULTS (ON UNSEEN TEST SET)")
    print("=" * 65)
    print(f"{'Model':<26} | {'MAE (kg)':<9} | {'RMSE (kg)':<9} | {'R²':<7} | {'vs Base':<9}")
    print("-" * 65)
    print(f"{'Decision Tree Regressor':<26} | {dt_mae:<9.3f} | {dt_rmse:<9.3f} | {dt_r2:<7.4f} | {dt_mae_improvement_pct:>+6.2f}%")
    print(f"{'Random Forest Regressor':<26} | {rf_mae:<9.3f} | {rf_rmse:<9.3f} | {rf_r2:<7.4f} | {rf_mae_improvement_pct:>+6.2f}%")
    print(f"{'Historical Mean Baseline':<26} | {base_mae:<9.3f} | {base_rmse:<9.3f} | {base_r2:<7.4f} | {'0.00%':>7}")
    print("=" * 65)
    print(f"Outcome: {best_model_name} achieves the best predictive performance on the test set.")
    print("-" * 65)
    print(f"High-Waste Classifier Accuracy:  {cls_acc*100:.2f}%")
    print(f"High-Waste Classifier Precision: {cls_prec*100:.2f}%")
    print(f"High-Waste Classifier Recall:    {cls_rec*100:.2f}%")
    print(f"High-Waste Classifier F1-Score:  {cls_f1*100:.2f}%")
    print("=" * 65)
    print(f"Saved RF regressor pipeline to: {config.RF_MODEL_PATH}")
    print(f"Saved DT regressor pipeline to: {config.DT_MODEL_PATH}")
    print(f"Saved classifier pipeline to:   {config.CLASSIFIER_PATH}")
    print(f"Saved metadata to:              {config.MODEL_METADATA_PATH}")
    print(f"Saved comparison JSON to:       {config.MODEL_COMPARISON_JSON_PATH}")
    print(f"Saved comparison CSV to:        {config.MODEL_COMPARISON_CSV_PATH}")

    return metadata


if __name__ == "__main__":
    train_and_evaluate_models()
