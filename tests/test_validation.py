"""
Unit and Integration Tests for MongoDB Schema Validation and Domain Rules
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import pytest
from pymongo.errors import WriteError, OperationFailure

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_db
from database.validators import validate_meal_record_business_rules


@pytest.fixture(scope="module")
def db():
    return get_db()


def test_mongodb_schema_rejects_negative_leftover(db):
    """Verifies that MongoDB JSON Schema strictly blocks documents with negative leftovers."""
    invalid_record = {
        "meal_id": "TEST_INVALID_NEG_LEFTOVER",
        "meal_date": "2026-10-15",
        "meal_type": "Lunch",
        "day_of_week": "Thursday",
        "expected_attendance": 600,
        "actual_attendance": 580,
        "menu_items": [
            {
                "item_name": "Rice",
                "category": "Rice & Breads",
                "prepared_kg": 50.0,
                "leftover_kg": -5.0  # Invalid
            }
        ],
        "total_prepared_kg": 150.0,
        "total_served_kg": 140.0,
        "total_leftover_kg": -5.0,  # Invalid: negative
        "recorded_at": datetime.now(timezone.utc)
    }

    with pytest.raises((WriteError, OperationFailure)):
        db["meal_records"].insert_one(invalid_record)


def test_mongodb_schema_rejects_invalid_meal_type(db):
    """Verifies that MongoDB JSON Schema blocks disallowed meal types."""
    invalid_record = {
        "meal_id": "TEST_INVALID_MEAL_TYPE",
        "meal_date": "2026-10-15",
        "meal_type": "Brunch",  # Disallowed
        "day_of_week": "Thursday",
        "expected_attendance": 600,
        "actual_attendance": 580,
        "menu_items": [
            {
                "item_name": "Rice",
                "category": "Rice & Breads",
                "prepared_kg": 50.0,
                "leftover_kg": 5.0
            }
        ],
        "total_prepared_kg": 150.0,
        "total_served_kg": 140.0,
        "total_leftover_kg": 10.0,
        "recorded_at": datetime.now(timezone.utc)
    }

    with pytest.raises((WriteError, OperationFailure)):
        db["meal_records"].insert_one(invalid_record)


def test_python_business_rule_capacity_exceeded():
    """Verifies Python business rule catches attendance exceeding hall capacity."""
    record = {
        "expected_attendance": 1300,
        "actual_attendance": 1450,  # Exceeds default 1200
        "total_prepared_kg": 500.0,
        "total_served_kg": 450.0,
        "total_leftover_kg": 50.0,
        "menu_items": []
    }
    is_valid, errors = validate_meal_record_business_rules(record, max_capacity=1200)
    assert not is_valid
    assert any("exceeds maximum hall capacity" in err for err in errors)


def test_python_business_rule_mass_conservation_violation():
    """Verifies Python business rule catches served + leftover > prepared."""
    record = {
        "expected_attendance": 500,
        "actual_attendance": 480,
        "total_prepared_kg": 100.0,
        "total_served_kg": 95.0,
        "total_leftover_kg": 35.0,  # 95 + 35 = 130 > 100 * 1.05
        "menu_items": []
    }
    is_valid, errors = validate_meal_record_business_rules(record)
    assert not is_valid
    assert any("Physically implausible" in err for err in errors)
