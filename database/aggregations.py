"""
MongoDB Aggregation Pipelines Module
Implements analytical pipelines covering meal types, daily trends, itemized unwinding,
attendance bands, weekday/weekend comparisons, and financial waste impact.
"""

from typing import List, Dict, Any
from pymongo.database import Database
import config


# =====================================================================
# Aggregation 1: Average Leftovers by Meal Type
# =====================================================================
def get_leftovers_by_meal_type(db: Database) -> List[Dict[str, Any]]:
    """
    Groups meal records by meal_type (Breakfast, Lunch, Snacks, Dinner).
    Computes total meals, avg leftover, total leftover, avg prepared, and leftover rate.
    """
    pipeline = [
        {
            "$group": {
                "_id": "$meal_type",
                "meal_count": {"$sum": 1},
                "total_prepared_kg": {"$sum": "$total_prepared_kg"},
                "avg_prepared_kg": {"$avg": "$total_prepared_kg"},
                "total_leftover_kg": {"$sum": "$total_leftover_kg"},
                "avg_leftover_kg": {"$avg": "$total_leftover_kg"},
                "avg_expected_attendance": {"$avg": "$expected_attendance"},
                "avg_actual_attendance": {"$avg": "$actual_attendance"}
            }
        },
        {
            "$project": {
                "meal_type": "$_id",
                "_id": 0,
                "meal_count": 1,
                "total_prepared_kg": {"$round": ["$total_prepared_kg", 2]},
                "avg_prepared_kg": {"$round": ["$avg_prepared_kg", 2]},
                "total_leftover_kg": {"$round": ["$total_leftover_kg", 2]},
                "avg_leftover_kg": {"$round": ["$avg_leftover_kg", 2]},
                "avg_expected_attendance": {"$round": ["$avg_expected_attendance", 1]},
                "avg_actual_attendance": {"$round": ["$avg_actual_attendance", 1]},
                "leftover_percentage": {
                    "$round": [
                        {
                            "$multiply": [
                                {"$divide": ["$total_leftover_kg", {"$cond": [{"$eq": ["$total_prepared_kg", 0]}, 1, "$total_prepared_kg"]}]},
                                100
                            ]
                        },
                        2
                    ]
                }
            }
        },
        {"$sort": {"avg_leftover_kg": -1}}
    ]
    return list(db["meal_records"].aggregate(pipeline))


# =====================================================================
# Aggregation 2: Daily Food Waste Trends
# =====================================================================
def get_daily_food_waste_trends(db: Database, limit_days: int = 30) -> List[Dict[str, Any]]:
    """
    Groups records by calendar date (meal_date) to track daily preparation,
    leftovers, plate waste, and daily leftover percentage.
    """
    pipeline = [
        {
            "$group": {
                "_id": "$meal_date",
                "meals_served_count": {"$sum": 1},
                "total_prepared_kg": {"$sum": "$total_prepared_kg"},
                "total_leftover_kg": {"$sum": "$total_leftover_kg"},
                "total_plate_waste_kg": {"$sum": {"$ifNull": ["$total_waste_kg", 0.0]}},
                "total_diners": {"$sum": "$actual_attendance"}
            }
        },
        {
            "$project": {
                "date": "$_id",
                "_id": 0,
                "meals_served_count": 1,
                "total_prepared_kg": {"$round": ["$total_prepared_kg", 2]},
                "total_leftover_kg": {"$round": ["$total_leftover_kg", 2]},
                "total_plate_waste_kg": {"$round": ["$total_plate_waste_kg", 2]},
                "total_diners": 1,
                "waste_percentage": {
                    "$round": [
                        {
                            "$multiply": [
                                {
                                    "$divide": [
                                        "$total_leftover_kg",
                                        {"$cond": [{"$eq": ["$total_prepared_kg", 0]}, 1, "$total_prepared_kg"]}
                                    ]
                                },
                                100
                            ]
                        },
                        2
                    ]
                }
            }
        },
        {"$sort": {"date": -1}},
        {"$limit": limit_days},
        {"$sort": {"date": 1}}
    ]
    return list(db["meal_records"].aggregate(pipeline))


# =====================================================================
# Aggregation 3: Food Items with Highest Leftover Quantities
# =====================================================================
def get_top_wasted_food_items(db: Database, top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Uses $unwind on menu_items array.
    Groups by item name and category to identify items with highest cumulative waste.
    """
    pipeline = [
        {"$unwind": "$menu_items"},
        {
            "$group": {
                "_id": {
                    "item_name": "$menu_items.item_name",
                    "category": "$menu_items.category"
                },
                "times_served": {"$sum": 1},
                "total_prepared_kg": {"$sum": "$menu_items.prepared_kg"},
                "total_leftover_kg": {"$sum": "$menu_items.leftover_kg"},
                "avg_leftover_kg": {"$avg": "$menu_items.leftover_kg"}
            }
        },
        {
            "$project": {
                "item_name": "$_id.item_name",
                "category": "$_id.category",
                "_id": 0,
                "times_served": 1,
                "total_prepared_kg": {"$round": ["$total_prepared_kg", 2]},
                "total_leftover_kg": {"$round": ["$total_leftover_kg", 2]},
                "avg_leftover_kg": {"$round": ["$avg_leftover_kg", 2]},
                "leftover_percentage": {
                    "$round": [
                        {
                            "$multiply": [
                                {
                                    "$divide": [
                                        "$total_leftover_kg",
                                        {"$cond": [{"$eq": ["$total_prepared_kg", 0]}, 1, "$total_prepared_kg"]}
                                    ]
                                },
                                100
                            ]
                        },
                        2
                    ]
                }
            }
        },
        {"$sort": {"total_leftover_kg": -1}},
        {"$limit": top_n}
    ]
    return list(db["meal_records"].aggregate(pipeline))


# =====================================================================
# Aggregation 4: Attendance Bands Versus Leftovers
# =====================================================================
def get_attendance_vs_leftovers_bands(db: Database) -> List[Dict[str, Any]]:
    """
    Segments meal records into attendance tiers: Low (<450), Medium (450-700),
    High (700-950), and Very High (>950).
    Demonstrates correlation between attendance estimation deviations and surplus food.
    """
    pipeline = [
        {
            "$project": {
                "expected_attendance": 1,
                "actual_attendance": 1,
                "total_prepared_kg": 1,
                "total_leftover_kg": 1,
                "attendance_error": {"$subtract": ["$expected_attendance", "$actual_attendance"]},
                "attendance_band": {
                    "$switch": {
                        "branches": [
                            {"case": {"$lt": ["$actual_attendance", 450]}, "then": "1. Low (<450)"},
                            {
                                "case": {
                                    "$and": [
                                        {"$gte": ["$actual_attendance", 450]},
                                        {"$lt": ["$actual_attendance", 700]}
                                    ]
                                },
                                "then": "2. Medium (450-700)"
                            },
                            {
                                "case": {
                                    "$and": [
                                        {"$gte": ["$actual_attendance", 700]},
                                        {"$lt": ["$actual_attendance", 950]}
                                    ]
                                },
                                "then": "3. High (700-950)"
                            }
                        ],
                        "default": "4. Very High (950+)"
                    }
                }
            }
        },
        {
            "$group": {
                "_id": "$attendance_band",
                "meal_count": {"$sum": 1},
                "avg_expected_attendance": {"$avg": "$expected_attendance"},
                "avg_actual_attendance": {"$avg": "$actual_attendance"},
                "avg_overestimation_error": {"$avg": "$attendance_error"},
                "avg_prepared_kg": {"$avg": "$total_prepared_kg"},
                "avg_leftover_kg": {"$avg": "$total_leftover_kg"},
                "total_leftover_kg": {"$sum": "$total_leftover_kg"}
            }
        },
        {
            "$project": {
                "attendance_band": "$_id",
                "_id": 0,
                "meal_count": 1,
                "avg_expected_attendance": {"$round": ["$avg_expected_attendance", 1]},
                "avg_actual_attendance": {"$round": ["$avg_actual_attendance", 1]},
                "avg_overestimation_error": {"$round": ["$avg_overestimation_error", 1]},
                "avg_prepared_kg": {"$round": ["$avg_prepared_kg", 2]},
                "avg_leftover_kg": {"$round": ["$avg_leftover_kg", 2]},
                "total_leftover_kg": {"$round": ["$total_leftover_kg", 2]}
            }
        },
        {"$sort": {"attendance_band": 1}}
    ]
    return list(db["meal_records"].aggregate(pipeline))


# =====================================================================
# Aggregation 5: Weekday and Weekend Analysis
# =====================================================================
def get_weekday_vs_weekend_analysis(db: Database) -> List[Dict[str, Any]]:
    """
    Compares food preparation and leftover behavior across Weekday vs Weekend.
    Uses $project, $cond, $group, $avg, $sum, and $sort.
    """
    pipeline = [
        {
            "$project": {
                "meal_type": 1,
                "day_of_week": 1,
                "total_prepared_kg": 1,
                "total_leftover_kg": 1,
                "actual_attendance": 1,
                "day_category": {
                    "$cond": [
                        {"$in": ["$day_of_week", ["Saturday", "Sunday"]]},
                        "Weekend",
                        "Weekday"
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$day_category",
                "meal_count": {"$sum": 1},
                "total_prepared_kg": {"$sum": "$total_prepared_kg"},
                "avg_prepared_kg": {"$avg": "$total_prepared_kg"},
                "total_leftover_kg": {"$sum": "$total_leftover_kg"},
                "avg_leftover_kg": {"$avg": "$total_leftover_kg"},
                "avg_attendance": {"$avg": "$actual_attendance"}
            }
        },
        {
            "$project": {
                "day_category": "$_id",
                "_id": 0,
                "meal_count": 1,
                "avg_attendance": {"$round": ["$avg_attendance", 1]},
                "avg_prepared_kg": {"$round": ["$avg_prepared_kg", 2]},
                "total_prepared_kg": {"$round": ["$total_prepared_kg", 2]},
                "avg_leftover_kg": {"$round": ["$avg_leftover_kg", 2]},
                "total_leftover_kg": {"$round": ["$total_leftover_kg", 2]},
                "leftover_percentage": {
                    "$round": [
                        {
                            "$multiply": [
                                {
                                    "$divide": [
                                        "$total_leftover_kg",
                                        {"$cond": [{"$eq": ["$total_prepared_kg", 0]}, 1, "$total_prepared_kg"]}
                                    ]
                                },
                                100
                            ]
                        },
                        2
                    ]
                }
            }
        },
        {"$sort": {"day_category": 1}}
    ]
    return list(db["meal_records"].aggregate(pipeline))


# =====================================================================
# Aggregation 6: Monthly Waste Summary & Financial Impact
# =====================================================================
def get_monthly_waste_summary(db: Database, cost_per_kg: float = config.ESTIMATED_COST_PER_KG) -> List[Dict[str, Any]]:
    """
    Groups meal records by year and month (derived from meal_date string YYYY-MM).
    Calculates total preparation, total leftover, plate waste, and monetary waste in INR.
    """
    pipeline = [
        {
            "$project": {
                "year_month": {"$substr": ["$meal_date", 0, 7]},
                "total_prepared_kg": 1,
                "total_leftover_kg": 1,
                "total_waste_kg": {"$ifNull": ["$total_waste_kg", 0.0]},
                "actual_attendance": 1
            }
        },
        {
            "$group": {
                "_id": "$year_month",
                "meals_count": {"$sum": 1},
                "total_prepared_kg": {"$sum": "$total_prepared_kg"},
                "total_leftover_kg": {"$sum": "$total_leftover_kg"},
                "total_plate_waste_kg": {"$sum": "$total_waste_kg"},
                "avg_leftover_kg": {"$avg": "$total_leftover_kg"},
                "total_diners": {"$sum": "$actual_attendance"}
            }
        },
        {
            "$project": {
                "month": "$_id",
                "_id": 0,
                "meals_count": 1,
                "total_prepared_kg": {"$round": ["$total_prepared_kg", 2]},
                "total_leftover_kg": {"$round": ["$total_leftover_kg", 2]},
                "total_plate_waste_kg": {"$round": ["$total_plate_waste_kg", 2]},
                "avg_leftover_kg": {"$round": ["$avg_leftover_kg", 2]},
                "total_diners": 1,
                "estimated_loss_inr": {
                    "$round": [{"$multiply": ["$total_leftover_kg", cost_per_kg]}, 2]
                },
                "waste_rate_pct": {
                    "$round": [
                        {
                            "$multiply": [
                                {
                                    "$divide": [
                                        "$total_leftover_kg",
                                        {"$cond": [{"$eq": ["$total_prepared_kg", 0]}, 1, "$total_prepared_kg"]}
                                    ]
                                },
                                100
                            ]
                        },
                        2
                    ]
                }
            }
        },
        {"$sort": {"month": 1}}
    ]
    return list(db["meal_records"].aggregate(pipeline))


# =====================================================================
# Aggregation 7 (Bonus): Top High-Waste Audit Records
# =====================================================================
def get_top_high_waste_records(db: Database, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieves top outlier meals with greatest leftover amounts."""
    pipeline = [
        {"$sort": {"total_leftover_kg": -1}},
        {"$limit": limit},
        {
            "$project": {
                "_id": 0,
                "meal_id": 1,
                "meal_date": 1,
                "meal_type": 1,
                "day_of_week": 1,
                "expected_attendance": 1,
                "actual_attendance": 1,
                "total_prepared_kg": 1,
                "total_leftover_kg": 1,
                "weather_condition": 1,
                "special_event": 1
            }
        }
    ]
    return list(db["meal_records"].aggregate(pipeline))


# =====================================================================
# Aggregation 8 (Bonus): Forecast Residual Analysis by Meal Type
# =====================================================================
def get_prediction_accuracy_by_meal_type(db: Database) -> List[Dict[str, Any]]:
    """
    Analyzes prediction accuracy from the 'predictions' collection for records
    where actual_leftover_kg has been observed.
    """
    pipeline = [
        {"$match": {"actual_leftover_kg": {"$exists": True, "$ne": None}}},
        {
            "$group": {
                "_id": "$target_meal_type",
                "evaluated_count": {"$sum": 1},
                "mean_absolute_error_kg": {"$avg": "$absolute_error_kg"},
                "avg_predicted_kg": {"$avg": "$predicted_leftover_kg"},
                "avg_actual_kg": {"$avg": "$actual_leftover_kg"}
            }
        },
        {
            "$project": {
                "meal_type": "$_id",
                "_id": 0,
                "evaluated_count": 1,
                "mean_absolute_error_kg": {"$round": ["$mean_absolute_error_kg", 2]},
                "avg_predicted_kg": {"$round": ["$avg_predicted_kg", 2]},
                "avg_actual_kg": {"$round": ["$avg_actual_kg", 2]}
            }
        },
        {"$sort": {"mean_absolute_error_kg": 1}}
    ]
    return list(db["predictions"].aggregate(pipeline))
