"""
Integration Tests for PyMongo CRUD Operations
Tests Create, Read, Update, Delete with transaction verification.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import pytest

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_db
from database.crud import (
    insert_meal_record,
    get_meal_by_id,
    get_meals_by_date,
    update_meal_attendance,
    update_prediction_with_actual,
    delete_meal_record,
    insert_prediction
)


@pytest.fixture(scope="module")
def db():
    return get_db()


def test_crud_full_lifecycle(db):
    """Executes an end-to-end Create -> Read -> Update -> Delete operational cycle."""
    test_id = "TEST_CRUD_LIFECYCLE_001"

    # Clean up prior test document if present
    db["meal_records"].delete_one({"meal_id": test_id})

    # 1. CREATE
    doc = {
        "meal_id": test_id,
        "meal_date": "2026-10-18",
        "meal_type": "Lunch",
        "day_of_week": "Sunday",
        "expected_attendance": 650,
        "actual_attendance": 620,
        "menu_items": [
            {
                "item_name": "Steamed Rice",
                "category": "Rice & Breads",
                "prepared_kg": 120.0,
                "leftover_kg": 15.0
            },
            {
                "item_name": "Dal Tadka",
                "category": "Curry & Dal",
                "prepared_kg": 80.0,
                "leftover_kg": 10.0
            }
        ],
        "total_prepared_kg": 200.0,
        "total_served_kg": 175.0,
        "total_leftover_kg": 25.0,
        "total_waste_kg": 7.5,
        "weather_condition": "Sunny",
        "special_event": False,
        "recorded_at": datetime.now(timezone.utc)
    }

    insert_res = insert_meal_record(db, doc)
    assert insert_res["success"] is True

    # 2. READ
    retrieved = get_meal_by_id(db, test_id)
    assert retrieved is not None
    assert retrieved["meal_id"] == test_id
    assert retrieved["total_prepared_kg"] == 200.0

    # 3. UPDATE
    upd_res = update_meal_attendance(db, test_id, 635)
    assert upd_res["success"] is True
    updated_doc = get_meal_by_id(db, test_id)
    assert updated_doc["actual_attendance"] == 635

    # 4. DELETE
    del_res = delete_meal_record(db, test_id)
    assert del_res["success"] is True
    assert get_meal_by_id(db, test_id) is None


def test_prediction_update_with_actual(db):
    """Tests updating an upcoming prediction document with post-meal actual results."""
    test_pred_id = "TEST_PRED_UPDATE_001"
    db["predictions"].delete_one({"prediction_id": test_pred_id})

    pred_doc = {
        "prediction_id": test_pred_id,
        "target_meal_date": "2026-10-18",
        "target_meal_type": "Dinner",
        "predicted_leftover_kg": 32.5,
        "predicted_waste_percentage": 10.8,
        "model_name": "RandomForestRegressor_v1",
        "model_version": "1.0.0",
        "prediction_created_at": datetime.now(timezone.utc)
    }
    insert_prediction(db, pred_doc)

    # Actual outcome observed: 35.0 kg
    update_res = update_prediction_with_actual(db, test_pred_id, actual_leftover_kg=35.0)
    assert update_res["success"] is True
    assert update_res["actual_leftover_kg"] == 35.0
    assert update_res["absolute_error_kg"] == 2.5

    # Clean up
    db["predictions"].delete_one({"prediction_id": test_pred_id})
