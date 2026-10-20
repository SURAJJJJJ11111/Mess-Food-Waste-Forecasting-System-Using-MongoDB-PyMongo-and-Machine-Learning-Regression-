"""
Unit and Integration Tests for Machine Learning Prediction Workflow
"""

import sys
from pathlib import Path
import pytest

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.predict import predict_meal_leftovers
from database.connection import get_db


@pytest.fixture(scope="module")
def db():
    return get_db()


def test_prediction_output_bounds(db):
    """Verifies that predicted leftovers are strictly non-negative and bounded."""
    pred = predict_meal_leftovers(
        meal_date="2026-10-20",
        meal_type="Dinner",
        day_of_week="Tuesday",
        expected_attendance=750,
        total_prepared_kg=350.0,
        weather_condition="Sunny",
        special_event=False,
        save_to_mongodb=False
    )
    assert "predicted_leftover_kg" in pred
    assert pred["predicted_leftover_kg"] >= 0.0
    assert pred["predicted_waste_percentage"] >= 0.0
    assert pred["suggested_preparation_kg"] > 0.0


def test_prediction_invalid_inputs():
    """Verifies that predict_meal_leftovers rejects negative attendance or quantities."""
    with pytest.raises(ValueError):
        predict_meal_leftovers(
            meal_date="2026-10-20",
            meal_type="Dinner",
            day_of_week="Tuesday",
            expected_attendance=-10,  # Invalid
            total_prepared_kg=350.0,
            save_to_mongodb=False
        )

    with pytest.raises(ValueError):
        predict_meal_leftovers(
            meal_date="2026-10-20",
            meal_type="MidnightBuffet",  # Invalid
            day_of_week="Tuesday",
            expected_attendance=500,
            total_prepared_kg=350.0,
            save_to_mongodb=False
        )


def test_prediction_persisted_to_mongodb(db):
    """Verifies that predictions are saved into the MongoDB predictions collection."""
    pred = predict_meal_leftovers(
        meal_date="2026-10-21",
        meal_type="Breakfast",
        day_of_week="Wednesday",
        expected_attendance=600,
        total_prepared_kg=180.0,
        weather_condition="Pleasant",
        save_to_mongodb=True,
        db=db
    )
    pred_id = pred["prediction_id"]
    saved = db["predictions"].find_one({"prediction_id": pred_id})
    assert saved is not None
    assert saved["target_meal_type"] == "Breakfast"
    assert saved["predicted_leftover_kg"] == pred["predicted_leftover_kg"]

    # Clean up test prediction
    db["predictions"].delete_one({"prediction_id": pred_id})


def test_decision_tree_prediction():
    """Verifies that Decision Tree regressor generates valid numerical predictions."""
    pred = predict_meal_leftovers(
        meal_date="2026-10-22",
        meal_type="Lunch",
        day_of_week="Thursday",
        expected_attendance=820,
        total_prepared_kg=420.0,
        weather_condition="Sunny",
        special_event=False,
        model_type="decision_tree",
        save_to_mongodb=False
    )
    assert "predicted_leftover_kg" in pred
    assert pred["predicted_leftover_kg"] >= 0.0
    assert pred["model_name"] == "DecisionTreeRegressor"
    assert "recommendations" in pred
    assert pred["recommendations"]["suggested_preparation_kg"] > 0.0
