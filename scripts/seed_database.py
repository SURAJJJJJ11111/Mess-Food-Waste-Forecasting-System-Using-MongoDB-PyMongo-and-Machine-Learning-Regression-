"""
Database Seeding Script
Bootstraps MongoDB collections with realistic meal records, menus,
attendance logs, and sample prediction records.
Safe to rerun: clears existing synthetic collections before repopulating.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import logging
from database.connection import get_db, check_connection
from database.setup import setup_database
from ml.generate_dataset import generate_synthetic_records, export_dataset_to_csv_and_json
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def seed_database(num_days: int = 375) -> None:
    """
    Seeds all 4 collections:
    1. 'meal_records' (~1,500 records)
    2. 'attendance_records' (~1,500 records)
    3. 'menus' (~1,500 records)
    4. 'predictions' (sample forecasts with evaluations)
    """
    ok, conn_info = check_connection()
    if not ok:
        logger.error(f"Cannot seed database: {conn_info}")
        sys.exit(1)

    logger.info(conn_info)
    db = get_db()

    # Apply Schema validation and indexes first
    logger.info("Initializing schema validators and indexes...")
    setup_database(db)

    # Clean existing collections before fresh seed
    logger.info("Purging existing documents in collections...")
    for col_name in ["meal_records", "attendance_records", "menus", "predictions"]:
        db[col_name].delete_many({})

    # Generate synthetic records
    logger.info(f"Generating synthetic records for {num_days} days...")
    records = generate_synthetic_records(num_days=num_days)
    export_dataset_to_csv_and_json(records)

    meal_docs = []
    att_docs = []
    menu_docs = []
    pred_docs = []

    for idx, r in enumerate(records):
        meal_id = r["meal_id"]
        date_str = r["meal_date"]
        meal_type = r["meal_type"]

        # Ensure recorded_at is datetime
        rec_dt = r["recorded_at"]
        if not isinstance(rec_dt, datetime):
            rec_dt = datetime.strptime(str(rec_dt)[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)

        # 1. Meal Record
        meal_docs.append({
            "meal_id": meal_id,
            "meal_date": date_str,
            "meal_type": meal_type,
            "day_of_week": r["day_of_week"],
            "expected_attendance": int(r["expected_attendance"]),
            "actual_attendance": int(r["actual_attendance"]),
            "menu_items": r["menu_items"],
            "total_prepared_kg": float(r["total_prepared_kg"]),
            "total_served_kg": float(r["total_served_kg"]),
            "total_leftover_kg": float(r["total_leftover_kg"]),
            "total_waste_kg": float(r["total_waste_kg"]),
            "weather_condition": r["weather_condition"],
            "special_event": bool(r["special_event"]),
            "recorded_at": rec_dt
        })

        # 2. Attendance Record
        att_docs.append({
            "attendance_id": f"ATT_{meal_id}",
            "meal_id": meal_id,
            "meal_date": date_str,
            "meal_type": meal_type,
            "expected_attendance": int(r["expected_attendance"]),
            "actual_attendance": int(r["actual_attendance"]),
            "attendance_source": "Biometric Turnstile"
        })

        # 3. Menu Record
        menu_items_planned = [
            {
                "item_name": item["item_name"],
                "category": item["category"],
                "planned_quantity_kg": item["prepared_kg"]
            }
            for item in r["menu_items"]
        ]
        menu_docs.append({
            "menu_id": f"MENU_{meal_id}",
            "meal_type": meal_type,
            "food_items": menu_items_planned,
            "menu_date": date_str,
            "estimated_students": int(r["expected_attendance"]),
            "created_at": rec_dt
        })

        # 4. Sample Predictions for every 10th meal
        if idx % 10 == 0:
            pred_leftover = round(r["total_leftover_kg"] * (0.90 + 0.20 * (idx % 7) / 7), 2)
            pred_waste_pct = round((pred_leftover / (r["total_prepared_kg"] or 1.0)) * 100, 2)
            abs_err = round(abs(pred_leftover - r["total_leftover_kg"]), 2)

            pred_docs.append({
                "prediction_id": f"PRED_{meal_id}",
                "target_meal_date": date_str,
                "target_meal_type": meal_type,
                "predicted_leftover_kg": float(pred_leftover),
                "predicted_waste_percentage": float(pred_waste_pct),
                "model_name": "RandomForestRegressor_v1",
                "model_version": "1.0.0",
                "prediction_created_at": rec_dt,
                "actual_leftover_kg": float(r["total_leftover_kg"]),
                "absolute_error_kg": float(abs_err)
            })

    logger.info(f"Inserting {len(meal_docs)} meal records...")
    db["meal_records"].insert_many(meal_docs, ordered=False)

    logger.info(f"Inserting {len(att_docs)} attendance records...")
    db["attendance_records"].insert_many(att_docs, ordered=False)

    logger.info(f"Inserting {len(menu_docs)} menus...")
    db["menus"].insert_many(menu_docs, ordered=False)

    logger.info(f"Inserting {len(pred_docs)} sample predictions...")
    db["predictions"].insert_many(pred_docs, ordered=False)

    logger.info("Database seeding successfully completed!")
    print("\n--- Seeding Summary ---")
    print(f"meal_records:        {db['meal_records'].count_documents({})}")
    print(f"attendance_records:  {db['attendance_records'].count_documents({})}")
    print(f"menus:               {db['menus'].count_documents({})}")
    print(f"predictions:         {db['predictions'].count_documents({})}")


if __name__ == "__main__":
    seed_database()
