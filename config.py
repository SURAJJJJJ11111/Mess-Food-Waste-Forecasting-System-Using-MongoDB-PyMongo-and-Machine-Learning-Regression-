"""
Application Configuration Module
Centralizes environment variables, database configuration, paths, and default parameters.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of Project
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# MongoDB Settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "mess_food_waste_db")

# Directory Paths
DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data")
MODEL_DIR = BASE_DIR / os.getenv("MODEL_DIR", "models")
REPORTS_DIR = BASE_DIR / os.getenv("REPORTS_DIR", "report")
SCREENSHOTS_DIR = BASE_DIR / "screenshots"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Operational Business Constants
MESS_CAPACITY = int(os.getenv("MESS_CAPACITY", "1200"))
ESTIMATED_COST_PER_KG = float(os.getenv("ESTIMATED_COST_PER_KG", "45.0"))  # in INR per kg

# Model Artifact Paths
MODEL_PATH = MODEL_DIR / "random_forest_regressor.joblib"
RF_MODEL_PATH = MODEL_DIR / "random_forest_regressor.joblib"
DT_MODEL_PATH = MODEL_DIR / "decision_tree_regressor.joblib"
MODEL_METADATA_PATH = MODEL_DIR / "model_metadata.json"
CLASSIFIER_PATH = MODEL_DIR / "high_waste_classifier.joblib"
MODEL_COMPARISON_JSON_PATH = REPORTS_DIR / "model_comparison.json"
MODEL_COMPARISON_CSV_PATH = REPORTS_DIR / "model_comparison.csv"

# Supported Meal Types and Categories
VALID_MEAL_TYPES = ["Breakfast", "Lunch", "Snacks", "Dinner"]
VALID_FOOD_CATEGORIES = ["Main Course", "Rice & Breads", "Curry & Dal", "Snack & Beverage", "Dessert & Salad"]
