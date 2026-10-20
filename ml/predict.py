"""
Prediction Inference Module
Provides functions to load the trained Random Forest model,
validate upcoming meal parameters, predict expected leftover food (kg),
enforce non-negative bounds, calculate percentage, and save forecasts to MongoDB.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd
from pymongo.database import Database

import config
from database.connection import get_db
from database.crud import insert_prediction
from ml.preprocessing import (
    engineer_features,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    HIGH_WASTE_THRESHOLD_KG
)

_cached_rf_regressor = None
_cached_dt_regressor = None
_cached_classifier = None


def get_trained_models(model_type: str = "random_forest"):
    """Loads and caches the model pipelines from disk."""
    global _cached_rf_regressor, _cached_dt_regressor, _cached_classifier

    # Load Random Forest
    if _cached_rf_regressor is None:
        if config.RF_MODEL_PATH.exists():
            _cached_rf_regressor = joblib.load(config.RF_MODEL_PATH)
        elif config.MODEL_PATH.exists():
            _cached_rf_regressor = joblib.load(config.MODEL_PATH)

    # Load Decision Tree
    if _cached_dt_regressor is None and config.DT_MODEL_PATH.exists():
        _cached_dt_regressor = joblib.load(config.DT_MODEL_PATH)

    # Load Classifier
    if _cached_classifier is None and config.CLASSIFIER_PATH.exists():
        _cached_classifier = joblib.load(config.CLASSIFIER_PATH)

    # Select requested regressor
    norm_type = str(model_type).lower().strip().replace(" ", "_")
    if "decision" in norm_type or "dt" in norm_type or "tree" in norm_type:
        if _cached_dt_regressor is None:
            if not config.DT_MODEL_PATH.exists():
                raise FileNotFoundError(f"Decision Tree model not found at {config.DT_MODEL_PATH}. Run ml/train_model.py first.")
            _cached_dt_regressor = joblib.load(config.DT_MODEL_PATH)
        selected_regressor = _cached_dt_regressor
        algo_name = "DecisionTreeRegressor"
    else:
        if _cached_rf_regressor is None:
            if not config.RF_MODEL_PATH.exists() and not config.MODEL_PATH.exists():
                raise FileNotFoundError(f"Random Forest model not found at {config.RF_MODEL_PATH}. Run ml/train_model.py first.")
            _cached_rf_regressor = joblib.load(config.RF_MODEL_PATH if config.RF_MODEL_PATH.exists() else config.MODEL_PATH)
        selected_regressor = _cached_rf_regressor
        algo_name = "RandomForestRegressor"

    return selected_regressor, _cached_classifier, algo_name


def predict_meal_leftovers(
    meal_date: Any = None,
    meal_type: Optional[str] = None,
    day_of_week: Optional[str] = None,
    expected_attendance: Optional[int] = None,
    total_prepared_kg: Optional[float] = None,
    weather_condition: str = "Sunny",
    special_event: bool = False,
    prev_leftover_kg: float = 20.0,
    prev_attendance: int = 650,
    model_type: str = "random_forest",
    save_to_mongodb: bool = True,
    persist: Optional[bool] = None,
    db: Optional[Database] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Generates a leftover food forecast for an upcoming meal using either
    Random Forest Regressor or Decision Tree Regressor.

    Accepts parameters either as a dictionary (first argument) or as keyword arguments.
    Ensures input validation, reproducible feature order, non-negative clipping,
    and optional persistence to MongoDB.
    """
    # Normalize input whether passed as dict or separate args
    if isinstance(meal_date, dict):
        d = meal_date
        m_date = str(d.get("meal_date", kwargs.get("meal_date", "")))
        m_type = str(d.get("meal_type", kwargs.get("meal_type", "")))
        d_week = str(d.get("day_of_week", kwargs.get("day_of_week", "")))
        exp_att = int(d.get("expected_attendance", kwargs.get("expected_attendance", 0)))
        prep_kg = float(d.get("total_prepared_kg", kwargs.get("total_prepared_kg", 0.0)))
        weather = str(d.get("weather_condition", kwargs.get("weather_condition", "Sunny")))
        sp_event = bool(d.get("special_event", kwargs.get("special_event", False)))
        prev_left = float(d.get("prev_leftover_kg", d.get("prev_meal_leftover_kg", kwargs.get("prev_leftover_kg", 20.0))))
        prev_att = int(d.get("prev_attendance", d.get("prev_meal_attendance", kwargs.get("prev_attendance", 650))))
        chosen_model = str(d.get("model_type", kwargs.get("model_type", model_type)))
    else:
        m_date = str(meal_date if meal_date is not None else kwargs.get("meal_date", ""))
        m_type = str(meal_type if meal_type is not None else kwargs.get("meal_type", ""))
        d_week = str(day_of_week if day_of_week is not None else kwargs.get("day_of_week", ""))
        exp_att = int(expected_attendance if expected_attendance is not None else kwargs.get("expected_attendance", 0))
        prep_kg = float(total_prepared_kg if total_prepared_kg is not None else kwargs.get("total_prepared_kg", 0.0))
        weather = str(weather_condition or kwargs.get("weather_condition", "Sunny"))
        sp_event = bool(special_event if special_event is not None else kwargs.get("special_event", False))
        prev_left = float(prev_leftover_kg if prev_leftover_kg is not None else kwargs.get("prev_leftover_kg", 20.0))
        prev_att = int(prev_attendance if prev_attendance is not None else kwargs.get("prev_attendance", 650))
        chosen_model = str(kwargs.get("model_type", model_type))

    # Handle persist parameter override
    should_save = persist if persist is not None else save_to_mongodb

    # 1. Validation
    if exp_att < 0:
        raise ValueError("Expected attendance cannot be negative.")
    if prep_kg < 0:
        raise ValueError("Planned preparation quantity cannot be negative.")
    if m_type not in config.VALID_MEAL_TYPES:
        raise ValueError(f"Invalid meal_type '{m_type}'. Permitted: {config.VALID_MEAL_TYPES}")

    reg_pipeline, cls_pipeline, algo_name = get_trained_models(chosen_model)

    # 2. Construct input DataFrame with exact features
    input_row = {
        "meal_date": m_date,
        "meal_type": m_type,
        "day_of_week": d_week,
        "expected_attendance": exp_att,
        "total_prepared_kg": prep_kg,
        "weather_condition": weather,
        "special_event": sp_event,
        "prev_leftover_kg": prev_left,
        "prev_attendance": prev_att
    }
    input_df = pd.DataFrame([input_row])
    featured_df = engineer_features(input_df)

    feature_cols = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
    X_input = featured_df[feature_cols]

    # 3. Predict leftover quantity (regression)
    raw_pred = float(reg_pipeline.predict(X_input)[0])
    # Physical Non-negative constraint: food surplus cannot be negative
    predicted_leftover_kg = max(0.0, round(raw_pred, 2))

    # Waste percentage denominator: total prepared food
    predicted_waste_pct = 0.0
    if prep_kg > 0:
        predicted_waste_pct = round((predicted_leftover_kg / prep_kg) * 100, 2)

    # 4. Predict high-waste risk (classification)
    is_high_waste_risk = predicted_leftover_kg > HIGH_WASTE_THRESHOLD_KG
    high_waste_probability = 0.0
    if cls_pipeline is not None:
        try:
            prob = cls_pipeline.predict_proba(X_input)[0][1]
            high_waste_probability = round(float(prob) * 100, 1)
        except Exception:
            pass

    # Actionable kitchen advice
    estimated_servings_wasted = int(predicted_leftover_kg / 0.40) if predicted_leftover_kg > 0 else 0
    suggested_preparation_kg = max(
        20.0,
        round(prep_kg - predicted_leftover_kg * 0.75, 1)
    )

    clean_date_tag = m_date.replace('-', '') if m_date else datetime.now().strftime('%Y%m%d')
    clean_type_tag = m_type.upper() if m_type else "MEAL"
    prediction_id = f"PRED_{clean_date_tag}_{clean_type_tag}_{datetime.now().strftime('%H%M%S')}"

    recommendations = {
        "estimated_servings_wasted": estimated_servings_wasted,
        "suggested_preparation_kg": suggested_preparation_kg,
        "recommended_action": (
            f"Scale preparation to {suggested_preparation_kg:.1f} kg to reduce risk of surplus."
            if is_high_waste_risk else "Planned preparation is optimal; maintain standard portions."
        )
    }

    result_doc = {
        "prediction_id": prediction_id,
        "target_meal_date": m_date,
        "target_meal_type": m_type,
        "predicted_leftover_kg": predicted_leftover_kg,
        "predicted_waste_percentage": predicted_waste_pct,
        "is_high_waste_risk": is_high_waste_risk,
        "high_waste_probability_pct": high_waste_probability,
        "estimated_servings_wasted": estimated_servings_wasted,
        "suggested_preparation_kg": suggested_preparation_kg,
        "recommendations": recommendations,
        "model_name": algo_name,
        "model_type": chosen_model,
        "model_version": "2.0.0",
        "prediction_created_at": datetime.now(timezone.utc)
    }

    # 5. Persist to MongoDB
    if should_save:
        target_db = db if db is not None else get_db()
        save_status = insert_prediction(target_db, result_doc)
        result_doc["saved_to_db"] = save_status.get("success", False)

    return result_doc


if __name__ == "__main__":
    print("Testing predictions with both algorithms on sample upcoming meal...\n")
    sample_params = {
        "meal_date": "2026-10-14",
        "meal_type": "Lunch",
        "day_of_week": "Wednesday",
        "expected_attendance": 850,
        "total_prepared_kg": 450.0,
        "weather_condition": "Pleasant",
        "special_event": False,
        "prev_leftover_kg": 22.0,
        "prev_attendance": 820
    }

    res_rf = predict_meal_leftovers(sample_params, model_type="random_forest", save_to_mongodb=False)
    print(f"Random Forest Prediction: {res_rf['predicted_leftover_kg']} kg (Model: {res_rf['model_name']})")

    res_dt = predict_meal_leftovers(sample_params, model_type="decision_tree", save_to_mongodb=False)
    print(f"Decision Tree Prediction: {res_dt['predicted_leftover_kg']} kg (Model: {res_dt['model_name']})")
