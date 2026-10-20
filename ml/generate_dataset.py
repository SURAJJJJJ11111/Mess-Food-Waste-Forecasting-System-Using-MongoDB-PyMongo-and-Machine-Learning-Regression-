"""
Synthetic Dataset Generator for Mess Food Waste Forecasting System
Generates physically consistent, temporally ordered meal operational records
with fixed random seed for 100% academic reproducibility.
All records are explicitly labeled with `data_source: 'SYNTHETIC_SIMULATION'`.
"""

import os
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to sys.path for direct script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import List, Dict, Any
import numpy as np
import pandas as pd
import config

RANDOM_SEED = 42

MEAL_CONFIGS = {
    "Breakfast": {
        "time": "08:00",
        "base_attendance": 650,
        "portion_kg": 0.28,
        "items": [
            ("Idli & Sambar", "Main Course", 0.40),
            ("Poha & Chutney", "Main Course", 0.30),
            ("Bread, Butter & Jam", "Snack & Beverage", 0.15),
            ("Tea & Coffee", "Snack & Beverage", 0.15),
        ]
    },
    "Lunch": {
        "time": "12:30",
        "base_attendance": 880,
        "portion_kg": 0.48,
        "items": [
            ("Steamed Basmati Rice", "Rice & Breads", 0.35),
            ("Dal Tadka & Rajma", "Curry & Dal", 0.25),
            ("Paneer Butter Masala", "Main Course", 0.20),
            ("Tawa Chapati", "Rice & Breads", 0.12),
            ("Green Salad & Curd", "Dessert & Salad", 0.08),
        ]
    },
    "Snacks": {
        "time": "17:00",
        "base_attendance": 520,
        "portion_kg": 0.22,
        "items": [
            ("Samosa & Mint Chutney", "Snack & Beverage", 0.45),
            ("Veg Grilled Sandwich", "Snack & Beverage", 0.35),
            ("Masala Chai", "Snack & Beverage", 0.20),
        ]
    },
    "Dinner": {
        "time": "20:00",
        "base_attendance": 820,
        "portion_kg": 0.46,
        "items": [
            ("Jeera Rice", "Rice & Breads", 0.32),
            ("Dal Makhani", "Curry & Dal", 0.25),
            ("Mix Veg Kadhai", "Main Course", 0.22),
            ("Butter Roti", "Rice & Breads", 0.13),
            ("Gulab Jamun", "Dessert & Salad", 0.08),
        ]
    }
}

WEATHER_CONDITIONS = ["Sunny", "Rainy", "Pleasant", "Cold"]
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def generate_synthetic_records(
    num_days: int = 375,
    start_date_str: str = "2025-01-01"
) -> List[Dict[str, Any]]:
    """
    Generates approximately 1,500 meal records (375 days * 4 meals/day = 1,500 meals).
    Enforces physically consistent conservation of mass:
    - total_prepared_kg = sum(items_prepared)
    - total_served_kg = min(actual_attendance * portion, prepared * 0.98)
    - total_leftover_kg = max(0.0, total_prepared_kg - total_served_kg)
    - total_waste_kg = actual plate waste discarded by diners (~3-5% of served)
    - Includes prior meal leftovers and attendance to allow sequential feature extraction.
    """
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    records: List[Dict[str, Any]] = []

    prev_leftover_kg = 15.0
    prev_attendance = 700

    meal_sequence = ["Breakfast", "Lunch", "Snacks", "Dinner"]

    for day_idx in range(num_days):
        current_date = start_date + timedelta(days=day_idx)
        date_str = current_date.strftime("%Y-%m-%d")
        day_of_week = DAYS_OF_WEEK[current_date.weekday()]
        is_weekend = day_of_week in ["Saturday", "Sunday"]

        # Weather factor
        weather = random.choices(
            WEATHER_CONDITIONS,
            weights=[0.45, 0.20, 0.25, 0.10],
            k=1
        )[0]

        # Special event probability (~8% of days, e.g. college fest, sports, exams)
        is_special_event = random.random() < 0.08

        for meal_type in meal_sequence:
            cfg = MEAL_CONFIGS[meal_type]
            base_att = cfg["base_attendance"]

            # Attendance adjustments:
            # - Weekends have lower mess attendance (students eat outside or go home)
            weekend_factor = 0.75 if is_weekend else 1.0
            # - Special events: fests drop mess attendance, exam days increase it slightly
            event_factor = 0.68 if is_special_event else 1.0
            # - Weather: rainy days keep students inside campus, boosting mess attendance
            weather_factor = 1.08 if weather == "Rainy" else 1.0

            expected_attendance = int(
                base_att * weekend_factor * event_factor * weather_factor
                + random.randint(-40, 40)
            )
            # Clip between plausible operational bounds
            expected_attendance = max(250, min(1150, expected_attendance))

            # Actual attendance deviates from expected due to unannounced student choices
            attendance_noise = int(np.random.normal(loc=-15, scale=45))
            actual_attendance = max(180, min(config.MESS_CAPACITY, expected_attendance + attendance_noise))

            # Head chef prepares food based on expected_attendance + safety buffer (5% to 15%)
            safety_buffer = random.uniform(1.05, 1.15)
            target_portion_kg = cfg["portion_kg"] * random.uniform(0.96, 1.04)
            total_prepared_kg = round(expected_attendance * target_portion_kg * safety_buffer, 2)

            # Actual consumption
            # Each actual diner consumes average portion with minor natural variation
            actual_per_capita = cfg["portion_kg"] * random.uniform(0.92, 1.02)
            actual_eaten_kg = round(actual_attendance * actual_per_capita, 2)

            # Served cannot exceed what was prepared
            total_served_kg = min(total_prepared_kg, actual_eaten_kg)

            # Leftover is edible surplus remaining in hot trays / kitchen
            total_leftover_kg = max(0.0, round(total_prepared_kg - total_served_kg, 2))

            # Plate waste (discarded by students) is ~3.5% to 5.5% of served food
            plate_waste_ratio = random.uniform(0.035, 0.055)
            total_waste_kg = round(total_served_kg * plate_waste_ratio, 2)

            # Generate item-level breakdown reconciling with totals
            items_list = []
            item_prep_sum = 0.0
            item_left_sum = 0.0

            for idx, (item_name, category, weight_share) in enumerate(cfg["items"]):
                item_prep = round(total_prepared_kg * weight_share, 2)
                item_left = round(total_leftover_kg * weight_share, 2)
                item_prep_sum += item_prep
                item_left_sum += item_left

                items_list.append({
                    "item_name": item_name,
                    "category": category,
                    "prepared_kg": item_prep,
                    "leftover_kg": item_left
                })

            # Adjust rounding difference on primary item
            diff_prep = round(total_prepared_kg - item_prep_sum, 2)
            diff_left = round(total_leftover_kg - item_left_sum, 2)
            if items_list:
                items_list[0]["prepared_kg"] = round(items_list[0]["prepared_kg"] + diff_prep, 2)
                items_list[0]["leftover_kg"] = round(max(0.0, items_list[0]["leftover_kg"] + diff_left), 2)

            meal_id = f"MEAL_{date_str.replace('-', '')}_{meal_type.upper()}"
            recorded_at_dt = datetime.strptime(f"{date_str} {cfg['time']}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)

            record = {
                "meal_id": meal_id,
                "meal_date": date_str,
                "meal_type": meal_type,
                "day_of_week": day_of_week,
                "expected_attendance": int(expected_attendance),
                "actual_attendance": int(actual_attendance),
                "menu_items": items_list,
                "total_prepared_kg": float(total_prepared_kg),
                "total_served_kg": float(total_served_kg),
                "total_leftover_kg": float(total_leftover_kg),
                "total_waste_kg": float(total_waste_kg),
                "weather_condition": weather,
                "special_event": bool(is_special_event),
                "prev_leftover_kg": float(prev_leftover_kg),
                "prev_attendance": int(prev_attendance),
                "recorded_at": recorded_at_dt,
                "data_source": "SYNTHETIC_SIMULATION"
            }
            records.append(record)

            # Update rolling sequential state
            prev_leftover_kg = total_leftover_kg
            prev_attendance = actual_attendance

    return records


def export_dataset_to_csv_and_json(records: List[Dict[str, Any]]) -> str:
    """Exports records to CSV and JSON formats in config.DATA_DIR."""
    csv_path = config.DATA_DIR / "historical_meal_records.csv"
    json_path = config.DATA_DIR / "historical_meal_records.json"

    # Flatten for CSV representation
    flat_rows = []
    for r in records:
        flat_rows.append({
            "meal_id": r["meal_id"],
            "meal_date": r["meal_date"],
            "meal_type": r["meal_type"],
            "day_of_week": r["day_of_week"],
            "expected_attendance": r["expected_attendance"],
            "actual_attendance": r["actual_attendance"],
            "total_prepared_kg": r["total_prepared_kg"],
            "total_served_kg": r["total_served_kg"],
            "total_leftover_kg": r["total_leftover_kg"],
            "total_waste_kg": r["total_waste_kg"],
            "weather_condition": r["weather_condition"],
            "special_event": r["special_event"],
            "prev_leftover_kg": r["prev_leftover_kg"],
            "prev_attendance": r["prev_attendance"],
            "data_source": r["data_source"]
        })

    df = pd.DataFrame(flat_rows)
    df.to_csv(csv_path, index=False)

    # Save JSON records (with datetime formatted as ISO)
    json_records = []
    for r in records:
        doc = dict(r)
        if isinstance(doc["recorded_at"], datetime):
            doc["recorded_at"] = doc["recorded_at"].isoformat()
        json_records.append(doc)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_records, f, indent=2)

    return str(csv_path)


if __name__ == "__main__":
    print(f"Generating synthetic mess food waste dataset with seed {RANDOM_SEED}...")
    dataset = generate_synthetic_records(num_days=375)
    csv_file = export_dataset_to_csv_and_json(dataset)
    print(f"Generated {len(dataset)} records. Saved to {csv_file}")
