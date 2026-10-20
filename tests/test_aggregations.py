"""
Integration Tests for MongoDB Aggregation Pipelines
"""

import sys
from pathlib import Path
import pytest

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_db
from database.aggregations import (
    get_leftovers_by_meal_type,
    get_daily_food_waste_trends,
    get_top_wasted_food_items,
    get_attendance_vs_leftovers_bands,
    get_weekday_vs_weekend_analysis,
    get_monthly_waste_summary
)


@pytest.fixture(scope="module")
def db():
    return get_db()


def test_aggregation_leftovers_by_meal_type(db):
    results = get_leftovers_by_meal_type(db)
    assert len(results) > 0
    meal_types = [r["meal_type"] for r in results]
    assert "Lunch" in meal_types
    assert "Dinner" in meal_types
    for r in results:
        assert "avg_leftover_kg" in r
        assert r["avg_leftover_kg"] >= 0


def test_aggregation_daily_trends(db):
    results = get_daily_food_waste_trends(db, limit_days=10)
    assert len(results) > 0
    first = results[0]
    assert "date" in first
    assert "total_prepared_kg" in first
    assert "waste_percentage" in first


def test_aggregation_top_wasted_items(db):
    results = get_top_wasted_food_items(db, top_n=5)
    assert len(results) == 5
    assert results[0]["total_leftover_kg"] >= results[-1]["total_leftover_kg"]
    for r in results:
        assert "item_name" in r
        assert "category" in r


def test_aggregation_attendance_bands(db):
    results = get_attendance_vs_leftovers_bands(db)
    assert len(results) > 0
    bands = [r["attendance_band"] for r in results]
    assert any("Low" in b for b in bands)
    for r in results:
        assert "avg_leftover_kg" in r


def test_aggregation_weekday_vs_weekend(db):
    results = get_weekday_vs_weekend_analysis(db)
    assert len(results) == 2
    categories = [r["day_category"] for r in results]
    assert "Weekday" in categories
    assert "Weekend" in categories


def test_aggregation_monthly_waste_summary(db):
    results = get_monthly_waste_summary(db)
    assert len(results) > 0
    for r in results:
        assert "month" in r
        assert "estimated_loss_inr" in r
        assert r["estimated_loss_inr"] >= 0
