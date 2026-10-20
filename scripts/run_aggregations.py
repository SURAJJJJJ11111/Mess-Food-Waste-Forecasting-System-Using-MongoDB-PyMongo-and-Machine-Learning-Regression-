"""
Aggregation Pipelines Execution and Demonstration Script
Executes all 6 required MongoDB aggregation pipelines + bonus pipelines,
displaying tabular results and academic explanations for viva demonstration.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from database.connection import get_db, check_connection
from database.aggregations import (
    get_leftovers_by_meal_type,
    get_daily_food_waste_trends,
    get_top_wasted_food_items,
    get_attendance_vs_leftovers_bands,
    get_weekday_vs_weekend_analysis,
    get_monthly_waste_summary,
    get_top_high_waste_records,
    get_prediction_accuracy_by_meal_type
)


def run_all_aggregations() -> None:
    ok, conn_info = check_connection()
    if not ok:
        print(f"Database error: {conn_info}")
        sys.exit(1)

    db = get_db()
    print("=" * 80)
    print("MESS FOOD WASTE FORECASTING SYSTEM - MONGODB AGGREGATION PIPELINES")
    print(f"Target Database: {db.name} | MongoDB Server Status: ONLINE")
    print("=" * 80)

    # -------------------------------------------------------------
    # 1. Leftovers by Meal Type
    # -------------------------------------------------------------
    print("\n[PIPELINE 1] Average Leftovers by Meal Type")
    print("Stages: $group (by meal_type) -> $project (averages & leftover %) -> $sort")
    res1 = get_leftovers_by_meal_type(db)
    df1 = pd.DataFrame(res1)
    print(df1.to_string(index=False))

    # -------------------------------------------------------------
    # 2. Daily Food Waste Trends (Recent 7 days sample)
    # -------------------------------------------------------------
    print("\n[PIPELINE 2] Daily Food Waste Trends (Sample Recent 7 Days)")
    print("Stages: $group (by meal_date) -> $project (totals & waste %) -> $sort -> $limit")
    res2 = get_daily_food_waste_trends(db, limit_days=7)
    df2 = pd.DataFrame(res2)
    print(df2.to_string(index=False))

    # -------------------------------------------------------------
    # 3. Top Wasted Food Items (Unwind)
    # -------------------------------------------------------------
    print("\n[PIPELINE 3] Food Items with Highest Leftover Quantities ($unwind)")
    print("Stages: $unwind (menu_items) -> $group (item_name, category) -> $project -> $sort -> $limit(10)")
    res3 = get_top_wasted_food_items(db, top_n=10)
    df3 = pd.DataFrame(res3)
    print(df3.to_string(index=False))

    # -------------------------------------------------------------
    # 4. Attendance Versus Leftovers Bands
    # -------------------------------------------------------------
    print("\n[PIPELINE 4] Attendance Bands Versus Leftovers ($switch conditional grouping)")
    print("Stages: $project ($switch for bands) -> $group -> $project -> $sort")
    res4 = get_attendance_vs_leftovers_bands(db)
    df4 = pd.DataFrame(res4)
    print(df4.to_string(index=False))

    # -------------------------------------------------------------
    # 5. Weekday vs Weekend Analysis
    # -------------------------------------------------------------
    print("\n[PIPELINE 5] Weekday versus Weekend Food Surplus Analysis")
    print("Stages: $project ($cond for weekend flag) -> $group -> $project -> $sort")
    res5 = get_weekday_vs_weekend_analysis(db)
    df5 = pd.DataFrame(res5)
    print(df5.to_string(index=False))

    # -------------------------------------------------------------
    # 6. Monthly Waste Summary & Financial Impact
    # -------------------------------------------------------------
    print("\n[PIPELINE 6] Monthly Food Waste & Financial Loss Summary ($substr & $multiply)")
    print("Stages: $project (extract year_month) -> $group -> $project (monetary INR loss) -> $sort")
    res6 = get_monthly_waste_summary(db)
    df6 = pd.DataFrame(res6)
    print(df6.head(8).to_string(index=False))

    # -------------------------------------------------------------
    # 7. Bonus: Top 5 Highest Waste Incidents Audit
    # -------------------------------------------------------------
    print("\n[PIPELINE 7 - BONUS] High Waste Incidents Audit (Top 5 Outliers)")
    print("Stages: $sort (total_leftover_kg: -1) -> $limit(5) -> $project")
    res7 = get_top_high_waste_records(db, limit=5)
    df7 = pd.DataFrame(res7)
    print(df7.to_string(index=False))

    # -------------------------------------------------------------
    # 8. Bonus: Model Accuracy Residuals by Meal Type
    # -------------------------------------------------------------
    print("\n[PIPELINE 8 - BONUS] Forecast MAE Residuals by Meal Type (predictions collection)")
    print("Stages: $match (evaluated actuals) -> $group (by target_meal_type) -> $project -> $sort")
    res8 = get_prediction_accuracy_by_meal_type(db)
    df8 = pd.DataFrame(res8)
    print(df8.to_string(index=False))

    print("\n" + "=" * 80)
    print("All 8 Aggregation Pipelines Executed Successfully on MongoDB!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_aggregations()
