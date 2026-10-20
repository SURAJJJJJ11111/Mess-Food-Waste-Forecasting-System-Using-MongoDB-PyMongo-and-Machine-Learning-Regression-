"""
Database Initialization and Schema Setup Script
Creates collections with strict JSON schema validators and sets up indexes.
Demonstrates rejection of invalid documents per CSE494 academic specification.
"""

import sys
from typing import Dict, Any
from pymongo.database import Database
from pymongo.errors import OperationFailure, WriteError
import logging

from database.connection import get_db, check_connection
from database.validators import COLLECTION_VALIDATORS
from database.indexes import setup_indexes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def setup_database(db: Database) -> bool:
    """
    Initializes collections with JSON schema validation rules and creates indexes.
    Safe to run idempotently (uses collMod if collection already exists).
    """
    existing_collections = db.list_collection_names()
    logger.info(f"Existing collections in '{db.name}': {existing_collections}")

    for col_name, validator in COLLECTION_VALIDATORS.items():
        if col_name not in existing_collections:
            logger.info(f"Creating collection '{col_name}' with JSON Schema validator...")
            try:
                db.create_collection(
                    col_name,
                    validator=validator,
                    validationLevel="strict",
                    validationAction="error"
                )
                logger.info(f"Collection '{col_name}' successfully created.")
            except OperationFailure as err:
                logger.warning(f"Could not create collection '{col_name}' with validator: {err}")
        else:
            logger.info(f"Collection '{col_name}' exists. Applying validator via collMod...")
            try:
                db.command({
                    "collMod": col_name,
                    "validator": validator,
                    "validationLevel": "strict",
                    "validationAction": "error"
                })
                logger.info(f"Updated validator for '{col_name}'.")
            except OperationFailure as err:
                logger.warning(f"collMod for '{col_name}' failed: {err}")

    # Set up indexes
    logger.info("Setting up unique and query performance indexes...")
    created_indexes = setup_indexes(db)
    for col, idx_list in created_indexes.items():
        logger.info(f"Indexes for '{col}': {idx_list}")

    logger.info(f"Database '{db.name}' schema and index configuration complete.")
    return True


def demonstrate_validation_rejection(db: Database) -> Dict[str, Any]:
    """
    Demonstrates MongoDB rejecting an invalid document that violates schema constraints:
    E.g., attempting to insert a meal record with a negative leftover quantity (-15.0 kg)
    and an invalid meal type ('MidnightFeast').
    """
    logger.info("--- Demonstrating MongoDB JSON Schema Enforcement ---")
    invalid_doc = {
        "meal_id": "TEST_INVALID_001",
        "meal_date": "2026-10-13",
        "meal_type": "MidnightFeast",  # INVALID: Not in enum [Breakfast, Lunch, Snacks, Dinner]
        "day_of_week": "Tuesday",
        "expected_attendance": 500,
        "actual_attendance": 480,
        "menu_items": [
            {
                "item_name": "Paneer Butter Masala",
                "category": "Main Course",
                "prepared_kg": 60.0,
                "leftover_kg": -15.0  # INVALID: Negative quantity
            }
        ],
        "total_prepared_kg": 150.0,
        "total_served_kg": 165.0,
        "total_leftover_kg": -15.0,  # INVALID: Negative quantity
        "recorded_at": "2026-10-13T21:00:00Z"  # INVALID: String instead of BSON Date
    }

    meals_col = db["meal_records"]
    rejection_result = {
        "tested_document": invalid_doc,
        "rejected": False,
        "rejection_reason": ""
    }

    try:
        meals_col.insert_one(invalid_doc)
        logger.error("Document unexpectedly inserted! Schema validation failed to trigger.")
        rejection_result["rejected"] = False
        rejection_result["rejection_reason"] = "Document was unexpectedly accepted by database."
    except (WriteError, OperationFailure) as err:
        logger.info(f"[SUCCESSFUL REJECTION] MongoDB rejected invalid document as expected!")
        logger.info(f"Rejection Error Code / Details: {err.details if hasattr(err, 'details') else err}")
        rejection_result["rejected"] = True
        rejection_result["rejection_reason"] = str(err)

    return rejection_result


if __name__ == "__main__":
    ok, status = check_connection()
    if not ok:
        print(f"Connection error: {status}")
        sys.exit(1)
    print(status)
    db = get_db()
    setup_database(db)
    rejection_test = demonstrate_validation_rejection(db)
    print("\nValidation Test Output Summary:")
    print(f"Rejected: {rejection_test['rejected']}")
    print(f"Reason: {rejection_test['rejection_reason'][:200]}...")
