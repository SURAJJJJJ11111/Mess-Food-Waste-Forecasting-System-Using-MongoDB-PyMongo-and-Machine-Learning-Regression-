"""
Model Evaluation and Diagnostic Plotting Script
Calculates test set regression metrics (MAE, RMSE, R2) for both
Random Forest Regressor and Decision Tree Regressor, compares against baseline,
and generates comprehensive visual diagnostic charts.
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

import config
from ml.preprocessing import (
    engineer_features,
    time_aware_train_test_split,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET_COLUMN
)
from ml.train_model import load_dataset_from_mongodb


def evaluate_models_and_compare() -> dict:
    """Evaluates Random Forest and Decision Tree on the identical test split."""
    raw_df = load_dataset_from_mongodb()
    featured_df = engineer_features(raw_df)
    train_df, test_df = time_aware_train_test_split(featured_df, test_ratio=0.20)

    feature_cols = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
    X_test = test_df[feature_cols]
    y_test = test_df[TARGET_COLUMN].values

    # 1. Evaluate Random Forest
    if not config.RF_MODEL_PATH.exists():
        raise FileNotFoundError(f"RF model not found at {config.RF_MODEL_PATH}. Run ml/train_model.py first.")
    rf_pipeline = joblib.load(config.RF_MODEL_PATH)
    y_pred_rf = np.clip(rf_pipeline.predict(X_test), 0.0, None)

    rf_mae = float(mean_absolute_error(y_test, y_pred_rf))
    rf_rmse = float(root_mean_squared_error(y_test, y_pred_rf))
    rf_r2 = float(r2_score(y_test, y_pred_rf))

    # 2. Evaluate Decision Tree
    if not config.DT_MODEL_PATH.exists():
        raise FileNotFoundError(f"DT model not found at {config.DT_MODEL_PATH}. Run ml/train_model.py first.")
    dt_pipeline = joblib.load(config.DT_MODEL_PATH)
    y_pred_dt = np.clip(dt_pipeline.predict(X_test), 0.0, None)

    dt_mae = float(mean_absolute_error(y_test, y_pred_dt))
    dt_rmse = float(root_mean_squared_error(y_test, y_pred_dt))
    dt_r2 = float(r2_score(y_test, y_pred_dt))

    # 3. Evaluate Baseline
    meal_type_means = train_df.groupby("meal_type")[TARGET_COLUMN].mean().to_dict()
    y_pred_base = test_df["meal_type"].map(meal_type_means).values

    base_mae = float(mean_absolute_error(y_test, y_pred_base))
    base_rmse = float(root_mean_squared_error(y_test, y_pred_base))
    base_r2 = float(r2_score(y_test, y_pred_base))

    rf_gain = round(((base_mae - rf_mae) / base_mae) * 100, 2)
    dt_gain = round(((base_mae - dt_mae) / base_mae) * 100, 2)

    return {
        "y_test": y_test,
        "y_pred_rf": y_pred_rf,
        "y_pred_dt": y_pred_dt,
        "y_pred_base": y_pred_base,
        "metrics": {
            "random_forest": {"mae": rf_mae, "rmse": rf_rmse, "r2": rf_r2, "gain": rf_gain},
            "decision_tree": {"mae": dt_mae, "rmse": dt_rmse, "r2": dt_r2, "gain": dt_gain},
            "baseline": {"mae": base_mae, "rmse": base_rmse, "r2": base_r2, "gain": 0.0}
        }
    }


def evaluate_and_plot() -> None:
    print("Evaluating models on test dataset and generating diagnostic charts...")
    eval_data = evaluate_models_and_compare()
    y_test = eval_data["y_test"]
    y_pred_rf = eval_data["y_pred_rf"]
    y_pred_dt = eval_data["y_pred_dt"]
    m = eval_data["metrics"]

    # Create 4-panel diagnostic visualization
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))

    max_val = max(np.max(y_test), np.max(y_pred_rf), np.max(y_pred_dt)) + 10

    # Panel 1: Actual vs Predicted Scatter
    ax1 = axes[0, 0]
    ax1.scatter(y_test, y_pred_dt, alpha=0.5, color="#8b5cf6", marker="^", s=35, label=f"Decision Tree (MAE: {m['decision_tree']['mae']:.2f} kg)")
    ax1.scatter(y_test, y_pred_rf, alpha=0.6, color="#0284c7", marker="o", s=30, label=f"Random Forest (MAE: {m['random_forest']['mae']:.2f} kg)")
    ax1.plot([0, max_val], [0, max_val], "r--", linewidth=2, label="Ideal 1:1 Line")
    ax1.set_xlabel("Actual Leftover (kg)", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Predicted Leftover (kg)", fontsize=11, fontweight="bold")
    ax1.set_title("Actual vs Predicted Food Leftovers (Unseen Test Set)", fontsize=12, fontweight="bold")
    ax1.legend(loc="upper left", frameon=True)
    ax1.set_xlim(0, max_val)
    ax1.set_ylim(0, max_val)

    # Panel 2: Residual Error Distributions
    ax2 = axes[0, 1]
    res_rf = y_test - y_pred_rf
    res_dt = y_test - y_pred_dt
    ax2.hist(res_dt, bins=25, alpha=0.5, color="#8b5cf6", edgecolor="black", label=f"Decision Tree Residuals (σ={np.std(res_dt):.2f})")
    ax2.hist(res_rf, bins=25, alpha=0.55, color="#0284c7", edgecolor="black", label=f"Random Forest Residuals (σ={np.std(res_rf):.2f})")
    ax2.axvline(0, color="red", linestyle="dashed", linewidth=2, label="Zero Error")
    ax2.set_xlabel("Prediction Error (Actual - Predicted) kg", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Frequency", fontsize=11, fontweight="bold")
    ax2.set_title("Residual Error Distributions (Test Set)", fontsize=12, fontweight="bold")
    ax2.legend(loc="upper right", frameon=True)

    # Panel 3: Error Metric Comparison (MAE & RMSE)
    ax3 = axes[1, 0]
    labels = ["Random Forest", "Decision Tree", "Baseline"]
    mae_vals = [m["random_forest"]["mae"], m["decision_tree"]["mae"], m["baseline"]["mae"]]
    rmse_vals = [m["random_forest"]["rmse"], m["decision_tree"]["rmse"], m["baseline"]["rmse"]]
    x = np.arange(len(labels))
    width = 0.35
    b1 = ax3.bar(x - width/2, mae_vals, width, label="MAE (kg)", color="#4f46e5", edgecolor="black", alpha=0.85)
    b2 = ax3.bar(x + width/2, rmse_vals, width, label="RMSE (kg)", color="#06b6d4", edgecolor="black", alpha=0.85)
    ax3.set_ylabel("Error in Kilograms (Lower is Better)", fontsize=11, fontweight="bold")
    ax3.set_title("Regression Error Comparison: MAE and RMSE", fontsize=12, fontweight="bold")
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels, fontsize=10, fontweight="bold")
    ax3.legend(frameon=True)
    for bar in b1 + b2:
        h = bar.get_height()
        ax3.annotate(f"{h:.2f}", xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Panel 4: R² Score Comparison
    ax4 = axes[1, 1]
    r2_vals = [m["random_forest"]["r2"], m["decision_tree"]["r2"], m["baseline"]["r2"]]
    colors_r2 = ["#10b981", "#8b5cf6", "#f59e0b"]
    bars_r2 = ax4.bar(labels, r2_vals, width=0.5, color=colors_r2, edgecolor="black", alpha=0.85)
    ax4.set_ylabel("R² Score (Higher is Better)", fontsize=11, fontweight="bold")
    ax4.set_title("Coefficient of Determination (R²) Comparison", fontsize=12, fontweight="bold")
    ax4.set_ylim(0, max(r2_vals) * 1.25)
    for bar in bars_r2:
        h = bar.get_height()
        ax4.annotate(f"{h:.4f}", xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.tight_layout()

    # Save to screenshots and report directories
    for plot_path in [
        config.SCREENSHOTS_DIR / "evaluation_metrics_plot.png",
        config.SCREENSHOTS_DIR / "07_evaluation_metrics_plot.png",
        config.REPORTS_DIR / "evaluation_metrics_plot.png"
    ]:
        plot_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(plot_path, dpi=300)
    plt.close()

    print("Saved evaluation diagnostic plots to:")
    print(f"  - {config.SCREENSHOTS_DIR / 'evaluation_metrics_plot.png'}")
    print(f"  - {config.REPORTS_DIR / 'evaluation_metrics_plot.png'}")


if __name__ == "__main__":
    evaluate_and_plot()
