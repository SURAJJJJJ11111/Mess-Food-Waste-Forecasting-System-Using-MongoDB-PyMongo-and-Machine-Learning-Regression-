"""
MongoDB Indexes Management Module
Creates and verifies unique indexes and query-performance compound indexes.
"""

from typing import List, Dict, Any
from pymongo.database import Database
from pymongo import ASCENDING, DESCENDING
import logging

logger = logging.getLogger(__name__)


def setup_indexes(db: Database) -> Dict[str, List[str]]:
    """
    Creates necessary unique constraints and query-optimization indexes for all collections.
    Returns a dictionary mapping collection names to the names of created indexes.
    """
    created_indexes: Dict[str, List[str]] = {}

    # 1. Menus Collection Indexes
    # - menu_id must be unique
    # - menu_date + meal_type composite unique index to prevent duplicate menus for same meal
    menus_col = db["menus"]
    idx_menu_id = menus_col.create_index([("menu_id", ASCENDING)], unique=True, name="idx_unique_menu_id")
    idx_menu_slot = menus_col.create_index(
        [("menu_date", ASCENDING), ("meal_type", ASCENDING)],
        unique=True,
        name="idx_unique_menu_date_meal"
    )
    created_indexes["menus"] = [idx_menu_id, idx_menu_slot]

    # 2. Meal Records Collection Indexes
    # - meal_id must be unique
    # - meal_date + meal_type composite unique index to ensure one operational record per meal
    # - query indexes on meal_date, meal_type, total_leftover_kg, day_of_week
    meals_col = db["meal_records"]
    idx_meal_id = meals_col.create_index([("meal_id", ASCENDING)], unique=True, name="idx_unique_meal_id")
    idx_meal_slot = meals_col.create_index(
        [("meal_date", ASCENDING), ("meal_type", ASCENDING)],
        unique=True,
        name="idx_unique_meal_date_type"
    )
    idx_meal_date = meals_col.create_index([("meal_date", DESCENDING)], name="idx_meal_date_desc")
    idx_meal_type_dow = meals_col.create_index(
        [("meal_type", ASCENDING), ("day_of_week", ASCENDING)],
        name="idx_meal_type_dow"
    )
    idx_meal_leftover = meals_col.create_index([("total_leftover_kg", DESCENDING)], name="idx_meal_leftover_desc")
    created_indexes["meal_records"] = [idx_meal_id, idx_meal_slot, idx_meal_date, idx_meal_type_dow, idx_meal_leftover]

    # 3. Attendance Records Collection Indexes
    att_col = db["attendance_records"]
    idx_att_id = att_col.create_index([("attendance_id", ASCENDING)], unique=True, name="idx_unique_attendance_id")
    idx_att_meal = att_col.create_index([("meal_id", ASCENDING)], unique=True, name="idx_unique_att_meal_id")
    idx_att_date_type = att_col.create_index(
        [("meal_date", ASCENDING), ("meal_type", ASCENDING)],
        name="idx_att_date_type"
    )
    created_indexes["attendance_records"] = [idx_att_id, idx_att_meal, idx_att_date_type]

    # 4. Predictions Collection Indexes
    preds_col = db["predictions"]
    idx_pred_id = preds_col.create_index([("prediction_id", ASCENDING)], unique=True, name="idx_unique_prediction_id")
    idx_pred_target = preds_col.create_index(
        [("target_meal_date", ASCENDING), ("target_meal_type", ASCENDING)],
        name="idx_pred_target_slot"
    )
    idx_pred_created = preds_col.create_index([("prediction_created_at", DESCENDING)], name="idx_pred_created_desc")
    created_indexes["predictions"] = [idx_pred_id, idx_pred_target, idx_pred_created]

    return created_indexes


def get_existing_indexes(db: Database) -> Dict[str, List[str]]:
    """Returns a dictionary listing existing index names for each collection."""
    result = {}
    for col_name in ["menus", "meal_records", "attendance_records", "predictions"]:
        if col_name in db.list_collection_names():
            result[col_name] = list(db[col_name].index_information().keys())
        else:
            result[col_name] = []
    return result
