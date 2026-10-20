"""
MongoDB CRUD Operations Module Using PyMongo
Encapsulates Create, Read, Update, and Delete operations with input validation,
proper projection, sorting, limits, and safe execution semantics.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import PyMongoError, DuplicateKeyError, WriteError
import logging

from database.validators import validate_meal_record_business_rules

logger = logging.getLogger(__name__)


# =====================================================================
# 1. CREATE Operations
# =====================================================================

def insert_menu(db: Database, menu_doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inserts a new menu document into 'menus' collection.
    Automatically attaches BSON datetime for created_at if not present.
    """
    doc = dict(menu_doc)
    if "created_at" not in doc or not isinstance(doc["created_at"], datetime):
        doc["created_at"] = datetime.now(timezone.utc)

    col: Collection = db["menus"]
    try:
        result = col.insert_one(doc)
        return {"success": True, "inserted_id": str(result.inserted_id), "menu_id": doc.get("menu_id")}
    except DuplicateKeyError as dke:
        return {"success": False, "error": f"Duplicate menu_id or date/type slot: {dke.details}"}
    except PyMongoError as err:
        return {"success": False, "error": str(err)}


def insert_meal_record(db: Database, meal_doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inserts a historical operational meal record into 'meal_records' collection.
    Applies Python domain reconciliation validation prior to database write.
    """
    # 1. Domain logic check
    is_valid, validation_errors = validate_meal_record_business_rules(meal_doc)
    if not is_valid:
        return {
            "success": False,
            "error": f"Business rule validation failed: {'; '.join(validation_errors)}"
        }

    doc = dict(meal_doc)
    if "recorded_at" not in doc or not isinstance(doc["recorded_at"], datetime):
        doc["recorded_at"] = datetime.now(timezone.utc)

    col: Collection = db["meal_records"]
    try:
        result = col.insert_one(doc)
        return {"success": True, "inserted_id": str(result.inserted_id), "meal_id": doc.get("meal_id")}
    except DuplicateKeyError as dke:
        return {"success": False, "error": f"Meal ID or slot already exists: {dke.details}"}
    except (WriteError, PyMongoError) as err:
        return {"success": False, "error": f"MongoDB Schema write failure: {str(err)}"}


def insert_meal_records_batch(db: Database, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Inserts a batch of meal records using insert_many for high-performance ingestion."""
    col: Collection = db["meal_records"]
    try:
        result = col.insert_many(records, ordered=False)
        return {"success": True, "count": len(result.inserted_ids)}
    except PyMongoError as err:
        return {"success": False, "error": str(err)}


def insert_attendance_record(db: Database, attendance_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Inserts an attendance verification document."""
    col: Collection = db["attendance_records"]
    try:
        result = col.insert_one(attendance_doc)
        return {"success": True, "inserted_id": str(result.inserted_id), "attendance_id": attendance_doc.get("attendance_id")}
    except PyMongoError as err:
        return {"success": False, "error": str(err)}


def insert_prediction(db: Database, prediction_doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Saves an upcoming meal forecast.
    Enforces non-negative prediction constraint and sets prediction_created_at.
    """
    doc = dict(prediction_doc)
    # Physical constraint: predicted leftover cannot be negative
    if doc.get("predicted_leftover_kg", 0.0) < 0.0:
        doc["predicted_leftover_kg"] = 0.0

    if "prediction_created_at" not in doc or not isinstance(doc["prediction_created_at"], datetime):
        doc["prediction_created_at"] = datetime.now(timezone.utc)

    col: Collection = db["predictions"]
    try:
        result = col.insert_one(doc)
        return {"success": True, "inserted_id": str(result.inserted_id), "prediction_id": doc.get("prediction_id")}
    except PyMongoError as err:
        return {"success": False, "error": str(err)}


# =====================================================================
# 2. READ Operations
# =====================================================================

def get_meal_by_id(db: Database, meal_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single meal record by its unique meal_id."""
    return db["meal_records"].find_one({"meal_id": meal_id}, {"_id": 0})


def get_meals_by_date(db: Database, meal_date: str) -> List[Dict[str, Any]]:
    """Retrieves all meal records for a specified date (YYYY-MM-DD)."""
    cursor = db["meal_records"].find({"meal_date": meal_date}, {"_id": 0}).sort("meal_type", 1)
    return list(cursor)


def get_meals_by_type(db: Database, meal_type: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Finds meal records filtered by meal type, sorted descending by date."""
    cursor = db["meal_records"].find({"meal_type": meal_type}, {"_id": 0}).sort("meal_date", -1).limit(limit)
    return list(cursor)


def get_meals_exceeding_leftover_threshold(db: Database, threshold_kg: float) -> List[Dict[str, Any]]:
    """
    Finds meal records where total leftovers exceeded the specified threshold in kg.
    Useful for audit logs and waste spike analysis.
    """
    query = {"total_leftover_kg": {"$gt": float(threshold_kg)}}
    projection = {
        "_id": 0,
        "meal_id": 1,
        "meal_date": 1,
        "meal_type": 1,
        "expected_attendance": 1,
        "actual_attendance": 1,
        "total_prepared_kg": 1,
        "total_leftover_kg": 1,
        "special_event": 1
    }
    cursor = db["meal_records"].find(query, projection).sort("total_leftover_kg", -1)
    return list(cursor)


def get_recent_meals(db: Database, limit: int = 20) -> List[Dict[str, Any]]:
    """Returns the most recent operational meal records."""
    cursor = db["meal_records"].find({}, {"_id": 0}).sort("meal_date", -1).limit(limit)
    return list(cursor)


def get_prediction_history(db: Database, limit: int = 50) -> List[Dict[str, Any]]:
    """Queries prediction logs sorted chronologically descending."""
    cursor = db["predictions"].find({}, {"_id": 0}).sort("prediction_created_at", -1).limit(limit)
    return list(cursor)


def get_all_menus(db: Database, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves scheduled menus."""
    cursor = db["menus"].find({}, {"_id": 0}).sort("menu_date", -1).limit(limit)
    return list(cursor)


# =====================================================================
# 3. UPDATE Operations
# =====================================================================

def update_meal_attendance(db: Database, meal_id: str, corrected_actual_attendance: int) -> Dict[str, Any]:
    """Corrects an incorrectly logged attendance count."""
    if corrected_actual_attendance < 0:
        return {"success": False, "error": "Attendance cannot be negative."}

    col: Collection = db["meal_records"]
    result = col.update_one(
        {"meal_id": meal_id},
        {"$set": {"actual_attendance": int(corrected_actual_attendance)}}
    )
    # Also update the corresponding attendance record if exists
    db["attendance_records"].update_one(
        {"meal_id": meal_id},
        {"$set": {"actual_attendance": int(corrected_actual_attendance)}}
    )
    return {
        "success": result.matched_count > 0,
        "matched_count": result.matched_count,
        "modified_count": result.modified_count
    }


def update_meal_prepared_quantity(db: Database, meal_id: str, new_prepared_kg: float) -> Dict[str, Any]:
    """Updates food preparation quantity for a meal."""
    if new_prepared_kg < 0:
        return {"success": False, "error": "Prepared quantity cannot be negative."}

    col: Collection = db["meal_records"]
    result = col.update_one(
        {"meal_id": meal_id},
        {"$set": {"total_prepared_kg": float(new_prepared_kg)}}
    )
    return {
        "success": result.matched_count > 0,
        "matched_count": result.matched_count,
        "modified_count": result.modified_count
    }


def record_actual_leftover(db: Database, meal_id: str, actual_leftover_kg: float, actual_waste_kg: float = 0.0) -> Dict[str, Any]:
    """Records post-meal leftover and plate-waste measurements for a meal record."""
    if actual_leftover_kg < 0:
        return {"success": False, "error": "Leftover quantity cannot be negative."}

    col: Collection = db["meal_records"]
    result = col.update_one(
        {"meal_id": meal_id},
        {
            "$set": {
                "total_leftover_kg": float(actual_leftover_kg),
                "total_waste_kg": float(actual_waste_kg)
            }
        }
    )
    return {
        "success": result.matched_count > 0,
        "modified_count": result.modified_count
    }


def update_prediction_with_actual(
    db: Database,
    prediction_id: str,
    actual_leftover_kg: float
) -> Dict[str, Any]:
    """
    Updates a forecast document with the post-meal actual outcome once observed.
    Calculates absolute error |predicted - actual|.
    """
    col: Collection = db["predictions"]
    pred_doc = col.find_one({"prediction_id": prediction_id})
    if not pred_doc:
        return {"success": False, "error": f"Prediction with ID '{prediction_id}' not found."}

    predicted_kg = float(pred_doc.get("predicted_leftover_kg", 0.0))
    abs_error = abs(predicted_kg - float(actual_leftover_kg))

    result = col.update_one(
        {"prediction_id": prediction_id},
        {
            "$set": {
                "actual_leftover_kg": float(actual_leftover_kg),
                "absolute_error_kg": round(abs_error, 2)
            }
        }
    )
    return {
        "success": True,
        "prediction_id": prediction_id,
        "predicted_kg": predicted_kg,
        "actual_leftover_kg": float(actual_leftover_kg),
        "absolute_error_kg": round(abs_error, 2),
        "modified_count": result.modified_count
    }


# =====================================================================
# 4. DELETE Operations
# =====================================================================

def delete_meal_record(db: Database, meal_id: str) -> Dict[str, Any]:
    """
    Deletes an operational meal record and maintains referential integrity
    by also removing associated attendance records.
    Safe deletion practices: requires explicit meal_id confirmation.
    """
    col: Collection = db["meal_records"]
    res = col.delete_one({"meal_id": meal_id})

    # Referential cascade on attendance records
    db["attendance_records"].delete_many({"meal_id": meal_id})

    return {
        "success": res.deleted_count > 0,
        "deleted_count": res.deleted_count,
        "meal_id": meal_id
    }


def delete_test_records_by_prefix(db: Database, prefix: str = "TEST_") -> Dict[str, int]:
    """Removes temporary or demonstration test records across collections."""
    regex_filter = {"$regex": f"^{prefix}"}
    m_res = db["meal_records"].delete_many({"meal_id": regex_filter})
    att_res = db["attendance_records"].delete_many({"attendance_id": regex_filter})
    pred_res = db["predictions"].delete_many({"prediction_id": regex_filter})
    menu_res = db["menus"].delete_many({"menu_id": regex_filter})

    return {
        "meal_records_deleted": m_res.deleted_count,
        "attendance_deleted": att_res.deleted_count,
        "predictions_deleted": pred_res.deleted_count,
        "menus_deleted": menu_res.deleted_count
    }
