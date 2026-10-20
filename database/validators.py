"""
MongoDB JSON Schema Validators and Python Domain Rule Validators
Enforces database-level structural and type constraints alongside business-level reconciliation logic.
"""

from typing import Dict, Any, Tuple, List
import config

# =====================================================================
# 1. MongoDB JSON Schema Validators
# =====================================================================

MENUS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["menu_id", "meal_type", "menu_date", "food_items", "estimated_students", "created_at"],
        "properties": {
            "menu_id": {
                "bsonType": "string",
                "description": "Unique menu identifier (e.g. MENU_20261013_LUNCH)"
            },
            "meal_type": {
                "enum": ["Breakfast", "Lunch", "Snacks", "Dinner"],
                "description": "Meal category must be Breakfast, Lunch, Snacks, or Dinner"
            },
            "menu_date": {
                "bsonType": "string",
                "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
                "description": "Date formatted as YYYY-MM-DD"
            },
            "estimated_students": {
                "bsonType": ["int", "long"],
                "minimum": 0,
                "maximum": 5000,
                "description": "Expected diners count between 0 and 5000"
            },
            "food_items": {
                "bsonType": "array",
                "minItems": 1,
                "description": "Array of food items planned for this menu",
                "items": {
                    "bsonType": "object",
                    "required": ["item_name", "category", "planned_quantity_kg"],
                    "properties": {
                        "item_name": {"bsonType": "string"},
                        "category": {
                            "enum": ["Main Course", "Rice & Breads", "Curry & Dal", "Snack & Beverage", "Dessert & Salad"]
                        },
                        "planned_quantity_kg": {
                            "bsonType": ["double", "int", "long"],
                            "minimum": 0.0,
                            "description": "Planned quantity in kg must be non-negative"
                        }
                    }
                }
            },
            "created_at": {
                "bsonType": "date",
                "description": "Timestamp when menu record was created"
            }
        }
    }
}

MEAL_RECORDS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "meal_id",
            "meal_date",
            "meal_type",
            "day_of_week",
            "expected_attendance",
            "actual_attendance",
            "menu_items",
            "total_prepared_kg",
            "total_served_kg",
            "total_leftover_kg",
            "recorded_at"
        ],
        "properties": {
            "meal_id": {
                "bsonType": "string",
                "description": "Unique meal identifier (e.g. MEAL_20261013_LUNCH)"
            },
            "meal_date": {
                "bsonType": "string",
                "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
                "description": "Meal date in YYYY-MM-DD format"
            },
            "meal_type": {
                "enum": ["Breakfast", "Lunch", "Snacks", "Dinner"],
                "description": "Meal category"
            },
            "day_of_week": {
                "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                "description": "Day of the week"
            },
            "expected_attendance": {
                "bsonType": ["int", "long"],
                "minimum": 0,
                "maximum": 5000,
                "description": "Expected headcount"
            },
            "actual_attendance": {
                "bsonType": ["int", "long"],
                "minimum": 0,
                "maximum": 5000,
                "description": "Actual headcount"
            },
            "menu_items": {
                "bsonType": "array",
                "minItems": 1,
                "description": "Itemized food items and breakdown",
                "items": {
                    "bsonType": "object",
                    "required": ["item_name", "category", "prepared_kg", "leftover_kg"],
                    "properties": {
                        "item_name": {"bsonType": "string"},
                        "category": {
                            "enum": ["Main Course", "Rice & Breads", "Curry & Dal", "Snack & Beverage", "Dessert & Salad"]
                        },
                        "prepared_kg": {
                            "bsonType": ["double", "int", "long"],
                            "minimum": 0.0
                        },
                        "leftover_kg": {
                            "bsonType": ["double", "int", "long"],
                            "minimum": 0.0
                        }
                    }
                }
            },
            "total_prepared_kg": {
                "bsonType": ["double", "int", "long"],
                "minimum": 0.0,
                "description": "Total edible food prepared in kg"
            },
            "total_served_kg": {
                "bsonType": ["double", "int", "long"],
                "minimum": 0.0,
                "description": "Total food served to diners in kg"
            },
            "total_leftover_kg": {
                "bsonType": ["double", "int", "long"],
                "minimum": 0.0,
                "description": "Edible surplus remaining unserved in kg"
            },
            "total_waste_kg": {
                "bsonType": ["double", "int", "long"],
                "minimum": 0.0,
                "description": "Plate waste / discarded food in kg"
            },
            "weather_condition": {
                "bsonType": "string",
                "description": "Weather condition (e.g. Sunny, Rainy, Pleasant, Cold)"
            },
            "special_event": {
                "bsonType": "bool",
                "description": "True if festival, sports day, or exam affected attendance"
            },
            "recorded_at": {
                "bsonType": "date",
                "description": "Timestamp when meal record was finalized"
            }
        }
    }
}

ATTENDANCE_RECORDS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "attendance_id",
            "meal_id",
            "meal_date",
            "meal_type",
            "expected_attendance",
            "actual_attendance",
            "attendance_source"
        ],
        "properties": {
            "attendance_id": {"bsonType": "string"},
            "meal_id": {"bsonType": "string"},
            "meal_date": {
                "bsonType": "string",
                "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
            },
            "meal_type": {
                "enum": ["Breakfast", "Lunch", "Snacks", "Dinner"]
            },
            "expected_attendance": {
                "bsonType": ["int", "long"],
                "minimum": 0
            },
            "actual_attendance": {
                "bsonType": ["int", "long"],
                "minimum": 0
            },
            "attendance_source": {
                "bsonType": "string",
                "description": "Source of attendance count (e.g. Biometric Turnstile, RFID Card, Manual Register)"
            }
        }
    }
}

PREDICTIONS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "prediction_id",
            "target_meal_date",
            "target_meal_type",
            "predicted_leftover_kg",
            "model_name",
            "model_version",
            "prediction_created_at"
        ],
        "properties": {
            "prediction_id": {"bsonType": "string"},
            "target_meal_date": {
                "bsonType": "string",
                "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
            },
            "target_meal_type": {
                "enum": ["Breakfast", "Lunch", "Snacks", "Dinner"]
            },
            "predicted_leftover_kg": {
                "bsonType": ["double", "int", "long"],
                "minimum": 0.0,
                "description": "Predicted edible leftover in kg, constrained to >= 0"
            },
            "predicted_waste_percentage": {
                "bsonType": ["double", "int", "long"],
                "minimum": 0.0,
                "maximum": 100.0,
                "description": "Forecasted leftover as % of planned preparation"
            },
            "model_name": {"bsonType": "string"},
            "model_version": {"bsonType": "string"},
            "prediction_created_at": {"bsonType": "date"},
            "actual_leftover_kg": {
                "bsonType": ["double", "int", "long"],
                "minimum": 0.0,
                "description": "Actual recorded leftover after meal occurs (populated post-meal)"
            },
            "absolute_error_kg": {
                "bsonType": ["double", "int", "long"],
                "minimum": 0.0,
                "description": "|predicted - actual| in kg (populated post-meal)"
            }
        }
    }
}

COLLECTION_VALIDATORS: Dict[str, Dict[str, Any]] = {
    "menus": MENUS_SCHEMA,
    "meal_records": MEAL_RECORDS_SCHEMA,
    "attendance_records": ATTENDANCE_RECORDS_SCHEMA,
    "predictions": PREDICTIONS_SCHEMA
}

# =====================================================================
# 2. Python-Level Business Logic Validation
# =====================================================================

def validate_meal_record_business_rules(
    record: Dict[str, Any],
    max_capacity: int = config.MESS_CAPACITY,
    tolerance_pct: float = 0.05
) -> Tuple[bool, List[str]]:
    """
    Validates physical and operational consistency rules that JSON Schema alone cannot enforce:
    1. Actual & Expected attendance within mess capacity.
    2. Sum of item prepared quantities reconciles with total_prepared_kg (within tolerance).
    3. Sum of item leftover quantities reconciles with total_leftover_kg (within tolerance).
    4. total_served_kg + total_leftover_kg does not physically exceed total_prepared_kg beyond tolerance.
    5. Non-negative quantities across all metrics.
    """
    errors: List[str] = []

    # Attendance bounds
    exp_att = record.get("expected_attendance", 0)
    act_att = record.get("actual_attendance", 0)

    if exp_att < 0:
        errors.append(f"Expected attendance cannot be negative (got {exp_att}).")
    if act_att < 0:
        errors.append(f"Actual attendance cannot be negative (got {act_att}).")
    if act_att > max_capacity:
        errors.append(
            f"Actual attendance ({act_att}) exceeds maximum hall capacity ({max_capacity})."
        )

    # Quantity checks
    prepared = float(record.get("total_prepared_kg", 0.0))
    served = float(record.get("total_served_kg", 0.0))
    leftover = float(record.get("total_leftover_kg", 0.0))
    waste = float(record.get("total_waste_kg", 0.0))

    if prepared < 0:
        errors.append(f"Total prepared cannot be negative (got {prepared} kg).")
    if served < 0:
        errors.append(f"Total served cannot be negative (got {served} kg).")
    if leftover < 0:
        errors.append(f"Total leftover cannot be negative (got {leftover} kg).")
    if waste < 0:
        errors.append(f"Total waste cannot be negative (got {waste} kg).")

    # Conservation of mass: served + leftover should be roughly equal to prepared
    # with acceptable tolerance due to moisture loss / serving variance
    allowed_max_total = prepared * (1.0 + tolerance_pct)
    if (served + leftover) > allowed_max_total and prepared > 0:
        errors.append(
            f"Physically implausible: served ({served:.1f} kg) + leftover ({leftover:.1f} kg) = "
            f"{(served + leftover):.1f} kg, exceeding total prepared ({prepared:.1f} kg) beyond {tolerance_pct*100}% tolerance."
        )

    # Itemized reconciliation
    menu_items = record.get("menu_items", [])
    if menu_items:
        items_prep_sum = sum(float(item.get("prepared_kg", 0.0)) for item in menu_items)
        items_left_sum = sum(float(item.get("leftover_kg", 0.0)) for item in menu_items)

        if prepared > 0 and abs(items_prep_sum - prepared) > (prepared * tolerance_pct + 1.0):
            errors.append(
                f"Item preparation sum ({items_prep_sum:.1f} kg) does not reconcile with "
                f"total_prepared_kg ({prepared:.1f} kg) within tolerance."
            )

        if leftover > 0 and abs(items_left_sum - leftover) > (leftover * tolerance_pct + 1.0):
            errors.append(
                f"Item leftover sum ({items_left_sum:.1f} kg) does not reconcile with "
                f"total_leftover_kg ({leftover:.1f} kg) within tolerance."
            )

    is_valid = len(errors) == 0
    return is_valid, errors
