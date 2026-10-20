# Mess Food Waste Forecasting System: Project Master Guide & Viva Defense Bible

**Course:** CSE494 – Intelligent NoSQL Databases (Continuous Assessment 2 - CA2)  
**Institution:** Lovely Professional University, Punjab, India  
**Topic:** Predictive Food Waste Forecasting & Operational Kitchen Surplus Reduction Using MongoDB, PyMongo, and Machine Learning Regression (Random Forest vs Decision Tree)  
**Technology Stack:** Python 3.12, MongoDB 8.x / Atlas, PyMongo v4, scikit-learn, Streamlit, Pandas, NumPy, Plotly, ReportLab, python-pptx

---

## Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [MongoDB Architecture & Document Design](#3-mongodb-architecture--document-design)
4. [BSON JSON Schema Validation ($jsonSchema)](#4-bson-json-schema-validation-jsonschema)
5. [MongoDB Indexing Strategy & Query Optimization](#5-mongodb-indexing-strategy--query-optimization)
6. [The 6 Core Analytical Aggregation Pipelines (Detailed Stage-by-Stage Breakdown)](#6-the-6-core-analytical-aggregation-pipelines)
7. [PyMongo CRUD Operations & Atomic Consistency](#7-pymongo-crud-operations--atomic-consistency)
8. [Machine Learning Engine: Regression Benchmark & Classifier](#8-machine-learning-engine-regression-benchmark--classifier)
9. [Streamlit Interactive Web Application Design](#9-streamlit-interactive-web-application-design)
10. [File-by-File Codebase Anatomy](#10-file-by-file-codebase-anatomy)
11. [Quick Numbers & Metrics Cheat Sheet (For Viva Memorization)](#11-quick-numbers--metrics-cheat-sheet)
12. [Comprehensive Faculty Viva Defense Guide (50+ Questions & Model Answers)](#12-comprehensive-faculty-viva-defense-guide)

---

## 1. Executive Summary & Problem Statement

### 1.1 The Campus Mess Problem
Institutional dining halls serving large student bodies (e.g., 1,200 diners across 4 daily meal sessions: Breakfast, Lunch, Snacks, Dinner) suffer from **chronic food overproduction**:
- **Baseline Inefficiency:** Standard mess operations prepare fixed portions based on registered student counts or static rule-of-thumb ratios, ignoring non-linear daily attendance variations.
- **Typical Waste:** 15% to 22% of prepared edible food remains unserved as surplus daily (~40 kg to 60 kg per meal session).
- **Financial Drain:** At an estimated production cost of ₹45 per kg, a 50 kg surplus per session results in ₹2,250 wasted per meal, ₹9,000 daily, and exceeding **₹2,70,000 per month**.
- **Environmental Impact:** Organic food rotting in landfills produces methane ($CH_4$), an aggressive greenhouse gas with 28x greater global warming potential than $CO_2$.

### 1.2 The Technological Solution
This project implements an end-to-end predictive food waste forecasting and operational management platform that integrates:
1. **MongoDB NoSQL Persistent Datastore:** Captures hierarchical, polymorphic meal sessions, weather conditions, attendance fluctuations, and itemized menu arrays within atomic BSON documents.
2. **Server-Side Aggregation Pipelines:** Employs 6 multi-stage aggregation pipelines to process historical metrics server-side, eliminating the latency of client-side Python data crunching.
3. **Machine Learning Regression Benchmark:** Trains and benchmarks **Random Forest Regressor** (100 bootstrap estimators) against **Decision Tree Regressor** (CART, regularized depth 6) and a historical mean baseline, enforcing zero data leakage.
4. **Auxiliary High-Waste Classifier:** Flags severe overproduction risk (>35 kg) with an **88.97% recall rate** so kitchen staff can initiate immediate buffer reductions.
5. **Interactive Streamlit Web Dashboard:** Provides real-time forecasts, scenario simulations, interactive Plotly visualizations, model switching, and full CRUD operations.

---

## 2. End-to-End System Architecture

```
                               ┌──────────────────────────────────────────────────┐
                               │             USER / MESS MANAGER                  │
                               └────────────────────────┬─────────────────────────┘
                                                        │ HTTP Requests
                                                        ▼
                               ┌──────────────────────────────────────────────────┐
                               │           STREAMLIT WEB DASHBOARD (app.py)       │
                               │  - Overview KPIs          - Prediction Simulator │
                               │  - Aggregation Visuals    - Dual Model Benchmark │
                               │  - Operational CRUD       - High-Waste Alerts    │
                               └──────────┬────────────────────────────┬──────────┘
                                          │                            │
                     Predictions & Models │                            │ PyMongo Driver
                                          ▼                            ▼
                 ┌──────────────────────────────────┐   ┌──────────────────────────────────┐
                 │       SCIKIT-LEARN ML ENGINE     │   │         PYMONGO DB ENGINE        │
                 │  - Random Forest Regressor       │   │  - Connection Pool (connection.py│
                 │  - Decision Tree Regressor       │   │  - JSON Schema Validators        │
                 │  - High-Waste Classifier (>35kg) │   │  - Composite Indexes             │
                 │  - Leakage-Free Preprocessing    │   │  - CRUD Manager (crud.py)        │
                 └────────────────┬─────────────────┘   └──────────────┬───────────────────┘
                                  │                                    │
                                  ▼ Serialized Artifacts               ▼ Native TCP Socket :27017
                 ┌──────────────────────────────────┐   ┌──────────────────────────────────┐
                 │          MODELS / DISK           │   │         MONGODB DATABASE         │
                 │  - random_forest_regressor.joblib│   │  Database: mess_food_waste_db    │
                 │  - decision_tree_regressor.joblib│   │  Collections:                    │
                 │  - high_waste_classifier.joblib  │   │   1. meal_records (Historical)   │
                 │  - model_metadata.json           │   │   2. predictions (Audit Trail)   │
                 └──────────────────────────────────┘   └──────────────────────────────────┘
```

---

## 3. MongoDB Architecture & Document Design

### 3.1 Why MongoDB Instead of Relational Databases (RDBMS)?
1. **Dynamic Nested Menus (1:Few Relationship):** A meal contains between 3 to 6 distinct dishes (e.g., Rice, Dal, Paneer, Chapati, Salad). In SQL, this requires 3 normalized tables (`meals`, `menu_items`, `dishes`) joined on every single read query. MongoDB embeds the `menu_items` array directly inside the meal document, granting $O(1)$ single-document reads without join latency.
2. **Atomic Single-Document Writes:** Updating a meal and its itemized leftover quantities occurs in a single atomic transaction without requiring multi-table ACID locks.
3. **Server-Side Aggregations:** MongoDB's Aggregation Framework provides dataflow pipelines (`$group`, `$unwind`, `$project`, `$switch`) executed natively in C++ inside the database server.
4. **JSON/BSON Interoperability:** Native dictionary serialization between Python, PyMongo, Streamlit, and MongoDB without complex ORM translation overhead.

### 3.2 BSON vs JSON
- **JSON (JavaScript Object Notation):** Text format supporting only string, number, boolean, array, object, null.
- **BSON (Binary JSON):** Binary serialization format used internally by MongoDB. Extends JSON with high-precision types:
  - UTC Date (`datetime.datetime`)
  - 64-bit Integers (`long`) and 64-bit IEEE 754 floating-point Doubles
  - `ObjectId` (12-byte unique identifier containing timestamp, machine ID, process ID, counter)
  - Raw binary data.

### 3.3 Core Document Schema (`meal_records`)
```json
{
  "_id": {"$oid": "67139a1b82f1b4c3e1000001"},
  "meal_id": "MEAL_20261019_LUNCH",
  "meal_date": "2026-10-19",
  "meal_type": "Lunch",
  "day_of_week": "Monday",
  "expected_attendance": 850,
  "actual_attendance": 780,
  "buffer_percentage": 10.0,
  "total_prepared_kg": 320.5,
  "total_leftover_kg": 42.0,
  "leftover_percentage": 13.1,
  "weather": {
    "temperature_c": 28.5,
    "condition": "Clear",
    "rainfall_mm": 0.0
  },
  "operational_flags": {
    "is_weekend": false,
    "is_exam_period": true,
    "is_holiday": false
  },
  "menu_items": [
    {"item_name": "Jeera Rice", "category": "Rice & Breads", "prepared_kg": 90.0, "leftover_kg": 14.5},
    {"item_name": "Paneer Butter Masala", "category": "Main Course", "prepared_kg": 110.0, "leftover_kg": 12.0},
    {"item_name": "Dal Tadka", "category": "Curry & Dal", "prepared_kg": 85.0, "leftover_kg": 11.5},
    {"item_name": "Tandoori Roti", "category": "Rice & Breads", "prepared_kg": 35.5, "leftover_kg": 4.0}
  ],
  "created_at": {"$date": "2026-10-19T13:45:00.000Z"}
}
```

### 3.4 Connection Pooling in `database/connection.py`
To ensure thread-safety and prevent connection starvation:
- Connects using `MongoClient(uri, maxPoolSize=50, minPoolSize=10, serverSelectionTimeoutMS=5000)`.
- Validates connectivity using `client.admin.command('ping')`.
- Implements a singleton getter `get_db()` ensuring all threads reuse the pool.

---

## 4. BSON JSON Schema Validation ($jsonSchema)

Schema validation is enforced at the database engine level in [database/validators.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/database/validators.py) and applied during [database/setup.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/database/setup.py).

### 4.1 Strict Constraints Enforced:
1. **Required Fields:** `meal_id`, `meal_date`, `meal_type`, `expected_attendance`, `actual_attendance`, `total_prepared_kg`, `total_leftover_kg`.
2. **Enum Enforcement:**
   - `meal_type` $\in$ `["Breakfast", "Lunch", "Snacks", "Dinner"]`.
   - `day_of_week` $\in$ `["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]`.
   - `menu_items.category` $\in$ `["Main Course", "Rice & Breads", "Curry & Dal", "Snack & Beverage", "Dessert & Salad"]`.
3. **Numeric Bounds:**
   - `total_prepared_kg`: `minimum: 0.0`.
   - `total_leftover_kg`: `minimum: 0.0`.
   - `expected_attendance`: `minimum: 0`, `maximum: 1500`.
   - `actual_attendance`: `minimum: 0`, `maximum: 1500`.
   - `buffer_percentage`: `minimum: 0.0`, `maximum: 50.0`.
4. **Date Pattern:** `meal_date` regex pattern `^[0-9]{4}-[0-9]{2}-[0-9]{2}$`.
5. **Application-Level Domain Validators:**
   - Leftover invariant: `total_prepared_kg >= total_leftover_kg`.
   - Itemized sum invariant: `sum(item['prepared_kg']) ≈ total_prepared_kg`.
   - Capacity constraint: `expected_attendance <= MESS_CAPACITY (1200)`.

---

## 5. MongoDB Indexing Strategy & Query Optimization

Defined in [database/indexes.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/database/indexes.py) and created upon initialization:

| Collection | Index Key | Type | Purpose / Query Optimization |
| :--- | :--- | :--- | :--- |
| `meal_records` | `{"meal_id": 1}` | **Unique Index** | Prevents duplicate ingestion of meal records |
| `meal_records` | `[("meal_date", 1), ("meal_type", 1)]` | **Compound Unique Index** | Guarantees business constraint: exactly 1 Breakfast/Lunch/Snacks/Dinner per date |
| `meal_records` | `{"meal_date": 1}` | **Single-Field B-Tree Index** | Accelerates date-range filtering in Aggregation 2 and Dashboard queries |
| `meal_records` | `{"meal_type": 1}` | **Single-Field B-Tree Index** | Optimizes `$group` by `meal_type` in Aggregation 1 |
| `meal_records` | `{"menu_items.item_name": 1}` | **Multikey Index** | Indexes individual elements within embedded arrays for fast menu search |
| `predictions` | `{"prediction_id": 1}` | **Unique Index** | Guarantees uniqueness of model audit logs |
| `predictions` | `{"created_at": -1}` | **Single-Field B-Tree Index** | Rapid retrieval of latest prediction history |

---

## 6. The 6 Core Analytical Aggregation Pipelines

Implemented in [database/aggregations.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/database/aggregations.py).

### Aggregation 1: Average Leftovers by Meal Type (`get_leftovers_by_meal_type`)
- **Objective:** Group all historical sessions by session type (Breakfast, Lunch, Snacks, Dinner) and calculate consumption and leftover metrics.
- **Pipeline Stages:**
  1. `$group`: Groups by `_id: "$meal_type"`. Computes `$sum` of `meal_count`, `$sum` and `$avg` of `total_prepared_kg`, `$sum` and `$avg` of `total_leftover_kg`, and average attendances.
  2. `$project`: Reshapes output, applies `$round` to 2 decimal places, and computes `leftover_percentage`:
     $$\text{leftover\_percentage} = \frac{\text{total\_leftover\_kg}}{\text{total\_prepared\_kg}} \times 100$$
  3. `$sort`: Orders by `avg_leftover_kg: -1`.
- **Key Finding:** Dinner generates the highest average leftover surplus (~28.4 kg / 16.2%), followed by Lunch (~22.1 kg / 12.8%).

### Aggregation 2: Daily Waste Trends (`get_daily_waste_trends`)
- **Objective:** Track aggregate leftover generation day-by-day over time to expose temporal shifts.
- **Pipeline Stages:**
  1. `$match` *(optional)*: Filters date range (`meal_date: {$gte: start, $lte: end}`).
  2. `$group`: Groups by `_id: "$meal_date"`. Accumulates total prepared, total leftover, and count of meals.
  3. `$project`: Formats fields and calculates daily leftover percentage.
  4. `$sort`: Orders chronologically `_id: 1` (`meal_date: 1`).
- **Use Case:** Powers the interactive Plotly time-series trend line on the dashboard.

### Aggregation 3: Top Wasted Food Items (`get_top_wasted_items`)
- **Objective:** Identify individual dishes that consistently produce the highest unserved waste.
- **Pipeline Stages:**
  1. `$unwind: "$menu_items"`: Deconstructs the embedded array of 3–5 items per meal, emitting 1 document per dish.
  2. `$group`: Groups by `_id: "$menu_items.item_name"`. Accumulates item category, times served, total prepared, and total leftover.
  3. `$project`: Calculates average leftover per serving and item waste percentage.
  4. `$sort`: Orders by `total_leftover_kg: -1`.
  5. `$limit: 10`: Returns the top 10 most wasted items.
- **Key Finding:** Perishable items and rice dishes (e.g., Jeera Rice, Dal Tadka, Kheer) exhibit the highest unserved volumes.

### Aggregation 4: Waste by Attendance Volume Band (`get_waste_by_attendance_band`)
- **Objective:** Determine if high-turnout or low-turnout meal sessions suffer higher leftover rates using the conditional `$switch` operator.
- **Pipeline Stages:**
  1. `$project`: Categorizes each meal into attendance tiers using `$switch`:
     - `< 500`: "Low Attendance (< 500)"
     - `500 - 800`: "Moderate Attendance (500-800)"
     - `> 800`: "High Attendance (> 800)"
  2. `$group`: Groups by `_id: "$attendance_band"`. Computes total and average leftovers.
  3. `$project`: Calculates waste rates and rounds metrics.
  4. `$sort`: Orders by `avg_leftover_kg: -1`.
- **Key Finding:** Low-attendance sessions exhibit the highest *percentage* of waste (up to 24%), because kitchen staff rarely downscale cooking proportionally.

### Aggregation 5: Weekend vs Weekday Operational Patterns (`get_weekend_vs_weekday_comparison`)
- **Objective:** Quantify operational waste divergence caused by students dining off-campus or leaving hostel on weekends.
- **Pipeline Stages:**
  1. `$project`: Maps `operational_flags.is_weekend` to `"Weekend"` or `"Weekday"` using `$cond`.
  2. `$group`: Groups by `_id: "$day_category"`. Computes average prepared, average attendance, and average leftovers.
  3. `$project`: Formats comparison metrics.
- **Key Finding:** Weekends feature an average attendance drop of ~220 students, yet meal preparation is only reduced by 8%, causing surplus waste spikes.

### Aggregation 6: Financial Loss Summary (`get_financial_loss_summary`)
- **Objective:** Convert physical food waste (in kilograms) into monetary loss (INR) and carbon emissions.
- **Pipeline Stages:**
  1. `$group`: Aggregates the entire collection (`_id: null`). Computes total meals, sum of prepared kg, and sum of leftover kg.
  2. `$project`: Multiplies total leftover kg by ₹45.0 (cost per kg):
     $$\text{Estimated Financial Loss (₹)} = \text{total\_leftover\_kg} \times 45.0$$
     $$\text{Estimated } CO_2 \text{ Equivalent (kg)} = \text{total\_leftover\_kg} \times 2.5$$

---

## 7. PyMongo CRUD Operations & Atomic Consistency

Implemented in [database/crud.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/database/crud.py):

1. **CREATE (`insert_meal_record`):**
   - Validates document structure against application rules.
   - Executes `collection.insert_one(record)`.
   - Returns inserted `_id` and `meal_id`. Rejects duplicates via unique indexes.
2. **READ (`get_meal_by_id`, `get_meals_by_date`):**
   - Uses indexed lookups `collection.find_one({"meal_id": meal_id})`.
   - Supports range queries with pagination: `collection.find(filter).skip(offset).limit(limit)`.
3. **UPDATE (`update_meal_attendance`, `update_prediction_with_actual`):**
   - Applies atomic field modifiers: `{"$set": {"actual_attendance": count, "updated_at": datetime.now(timezone.utc)}}`.
   - Never overwrites entire documents unnecessarily.
4. **DELETE (`delete_meal_record`):**
   - Executes `collection.delete_one({"meal_id": meal_id})`.
   - Returns boolean success confirmation based on `deleted_count == 1`.

---

## 8. Machine Learning Engine: Regression Benchmark & Classifier

Implemented across [ml/preprocessing.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/ml/preprocessing.py), [ml/train_model.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/ml/train_model.py), and [ml/predict.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/ml/predict.py).

### 8.1 Zero-Leakage Preprocessing Guarantee
- **Strict Leakage Prevention:** In forecasting, post-meal outcomes (`actual_attendance`, actual consumption) DO NOT EXIST when the kitchen prepares food.
- **Allowed Features (Pre-Meal Only):**
  - Numerical: `total_prepared_kg`, `expected_attendance`, `buffer_percentage`, `temperature_c`, `rainfall_mm`, `is_weekend`, `is_exam_period`, `is_holiday`, `month`, `day_of_month`.
  - Categorical: `meal_type`, `day_of_week`.
- **Target Variable ($y$):** `total_leftover_kg`.
- **ColumnTransformer Pipeline:**
  - `StandardScaler` applied to numerical features.
  - `OneHotEncoder(handle_unknown='ignore')` applied to categorical features.
  - Fitted STRICTLY on training split (1,200 records); applied to test split (301 records).

### 8.2 Dual Regression Model Benchmark

| Metric / Parameter | Random Forest Regressor | Decision Tree Regressor | Historical Mean Baseline |
| :--- | :--- | :--- | :--- |
| **Model Architecture** | Ensemble of 100 Bootstrap Trees | Single Decision Tree (CART) | Historical Average by Meal Type |
| **Hyperparameters** | `n_estimators=100`, `max_depth=12`, `min_samples_split=5` | `max_depth=6`, `min_samples_split=10`, `min_samples_leaf=5` | Groupby `meal_type` mean |
| **Mean Absolute Error (MAE)** | **14.229 kg** | **14.645 kg** | 15.412 kg |
| **Root Mean Squared Error (RMSE)** | **19.514 kg** | **19.683 kg** | 20.835 kg |
| **Coefficient of Determination ($R^2$)** | **0.4959** | **0.4871** | 0.4254 |
| **MAE Improvement vs Baseline** | **+7.68%** | **+4.98%** | 0.00% |
| **Variance / Generalization** | Low variance, robust against outliers | Susceptible to local variance | High bias, ignores operational flags |

### 8.3 Feature Importance Ranking (Random Forest)
1. `expected_attendance` (38.4%) – Dominant predictor of dining demand.
2. `total_prepared_kg` (29.1%) – Directly bounds maximum potential surplus.
3. `buffer_percentage` (11.8%) – Intentional kitchen overcook safety margin.
4. `meal_type_Dinner` / `Lunch` (8.2%) – Session-specific eating habits.
5. `is_weekend` (4.6%) – Student weekend departure impact.
6. `is_exam_period` (3.9%) – Exam schedule library stays & erratic dining.
7. Weather variables (`rainfall_mm`, `temperature_c`) (4.0%).

### 8.4 Auxiliary High-Waste Risk Classifier
- **Problem Formulation:** Predict whether unserved surplus will exceed severe threshold ($>35.0\text{ kg}$).
- **Algorithm:** `RandomForestClassifier(n_estimators=100, max_depth=8, class_weight='balanced')`.
- **Classification Performance:**
  - **Accuracy:** 83.39%
  - **Precision:** 77.56%
  - **Recall:** **88.97%** *(Optimized to avoid false negatives — we must never miss a severe waste event)*
  - **F1-Score:** 82.88%

---

## 9. Streamlit Interactive Web Application Design

The web interface in [app.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/app.py) features a 5-page structure with light/dark theme toggling:

1. **Dashboard Overview:** Real-time KPI summary tiles (Total Records in MongoDB, Total Food Prepared, Total Food Wasted, Overall Waste %, Total Financial Loss in ₹), meal-type distribution charts, and recent records table.
2. **Food Waste Analytics:** Interactive Plotly charts rendered directly from MongoDB Aggregation Pipelines (daily trends, top 10 wasted items, attendance bands, weekend vs weekday impact).
3. **Predict Future Leftovers:** Interactive forecasting form with dual model selection (Random Forest vs Decision Tree). Returns forecasted leftover kg, surplus percentage, high-waste risk alert, and actionable kitchen buffer recommendations. Logs predictions into MongoDB `predictions` collection.
4. **Model Benchmark & Viva Prep:** Side-by-side performance cards (MAE, RMSE, $R^2$), Actual vs. Predicted scatter plots, residual error distribution charts, and interactive technical viva question browser.
5. **Operational CRUD Management:** Full kitchen administrative interface to insert new meal records, search by `meal_id`, update attendance, or delete invalid documents with live schema validation.

---

## 10. File-by-File Codebase Anatomy

- [config.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/config.py): Centralized configuration module. Loads `.env`, declares MongoDB connection parameters, operational constants (`MESS_CAPACITY = 1200`, `ESTIMATED_COST_PER_KG = 45.0`), and path pointers.
- [app.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/app.py): Complete 5-page Streamlit web application.
- [database/connection.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/database/connection.py): Thread-safe MongoDB client singleton and connection pooling.
- [database/setup.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/database/setup.py): Creates collections, attaches `$jsonSchema` validators, and builds indexes.
- [database/validators.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/database/validators.py): MongoDB `$jsonSchema` specifications and Python domain validation functions.
- [database/indexes.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/database/indexes.py): Builds single, compound, and multikey indexes.
- [database/crud.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/database/crud.py): Atomic PyMongo Create, Read, Update, and Delete functions.
- [database/aggregations.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/database/aggregations.py): The 6 core analytical aggregation pipelines.
- [ml/generate_dataset.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/ml/generate_dataset.py): Realistic synthetic dataset generator producing 1,500 historical meal records (`Seed=42`).
- [ml/preprocessing.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/ml/preprocessing.py): Pre-meal feature engineering pipeline, standard scaler, and one-hot encoder.
- [ml/train_model.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/ml/train_model.py): Trains Random Forest Regressor, Decision Tree Regressor, Baseline, and Classifier; serializes models to `models/` and benchmark metrics to `report/`.
- [ml/predict.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/ml/predict.py): Dual-model inference module enforcing non-negative physical bounds ($0 \le \text{leftover} \le \text{prepared}$).
- [ml/evaluate.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/ml/evaluate.py): Generates 4-panel diagnostic scatter and residual error charts.
- [scripts/seed_database.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/scripts/seed_database.py): Bootstraps MongoDB with 1,500 records.
- [scripts/run_aggregations.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/scripts/run_aggregations.py): Standalone CLI demonstration runner for the 6 aggregation pipelines.
- [tests/](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/tests): Comprehensive test suite (21 unit and integration tests covering CRUD, aggregations, schema validation, and model comparison).
- [queries.mongodb.js](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/queries.mongodb.js): Native MongoDB Shell (`mongosh`) and Compass scripts.
- [report/generate_pdf_report.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/report/generate_pdf_report.py): ReportLab publication-ready academic PDF compiler.
- [report/generate_presentation.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/report/generate_presentation.py): Python-pptx 12-slide presentation deck compiler.

---

## 11. Quick Numbers & Metrics Cheat Sheet

Memorize these exact figures before entering your viva:

| Metric Name | Value to State | Context |
| :--- | :--- | :--- |
| **Mess Seating Capacity** | **1,200 diners** | Stored in `config.MESS_CAPACITY` |
| **Cost of Food per kg** | **₹45.0 per kg** | Estimated raw kitchen expenditure |
| **Total Records in Dataset** | **1,500 meals** | 1,200 Train (80%) / 301 Test (20%) |
| **Date Span of Dataset** | **~375 calendar days** | 4 meal sessions per day |
| **RF Regressor MAE** | **14.229 kg** | Mean Absolute Error on unseen test set |
| **RF Regressor RMSE** | **19.514 kg** | Root Mean Squared Error |
| **RF Regressor $R^2$** | **0.4959** | Explains ~50% of surplus variance |
| **RF Improvement vs Baseline**| **+7.68%** | Over Historical Mean Baseline (15.41 kg MAE) |
| **DT Regressor MAE** | **14.645 kg** | Decision Tree Regressor (Depth 6) |
| **High-Waste Alert Threshold**| **> 35.0 kg surplus** | High risk overproduction flag |
| **Classifier Recall** | **88.97%** | Crucial metric: catches 9 out of 10 waste spikes |
| **Classifier Accuracy** | **83.39%** | Overall binary classification accuracy |
| **Highest Wasting Meal** | **Dinner (~28.4 kg avg)** | Lowest attendance predictability |

---

## 12. Comprehensive Faculty Viva Defense Guide

### Section A: MongoDB Architecture & NoSQL Foundations

#### Q1: Why did you choose MongoDB instead of a Relational Database (RDBMS like MySQL or PostgreSQL)?
**Answer:**
1. **Polymorphic, Hierarchical Data:** Each meal session features an arbitrary number of dishes with variable categories and weights. In an RDBMS, this requires normalized multi-table schemas with foreign key `JOIN`s across `meals`, `menu_items`, and `dishes`. MongoDB's document model allows us to embed `menu_items` directly inside each meal document, giving $O(1)$ single-document reads with zero join latency.
2. **Atomic Single-Document Writes:** Preparation and leftover quantities can be written in a single atomic transaction without multi-table locking.
3. **Native Aggregation Pipelines:** Multi-stage aggregation pipelines (`$group`, `$unwind`, `$project`, `$switch`) run natively inside the database engine in C++, preventing the overhead of transferring thousands of raw records into Python memory.

#### Q2: What is BSON, and how does it differ from standard JSON?
**Answer:**
BSON stands for **Binary JSON**. While standard JSON is a human-readable text format supporting only 6 basic types (string, number, boolean, array, object, null), BSON is a binary serialization format used internally by MongoDB for storage and network transfer.  
Key advantages of BSON:
1. **Rich Data Types:** Directly supports native UTC dates (`datetime`), 64-bit integers (`long`), IEEE 754 doubles, and 12-byte `ObjectId`.
2. **Speed & Efficiency:** BSON stores length prefixes and field offsets, allowing MongoDB to traverse and skip fields without parsing every byte of text.

#### Q3: What is the structure of an `ObjectId` in MongoDB?
**Answer:**
An `ObjectId` is a 12-byte BSON identifier composed of:
- **4 bytes:** Unix timestamp representing document creation time.
- **5 bytes:** Random value unique to the machine and process.
- **3 bytes:** Incrementing counter, initialized to a random value.  
This guarantees cluster-wide uniqueness without centralized auto-increment locks.

#### Q4: Why did you embed `menu_items` inside `meal_records` instead of referencing a separate collection?
**Answer:**
We applied MongoDB's **1:Few Document Modeling Principle**:
- A typical meal contains only 3 to 6 distinct dishes (e.g., Rice, Dal, Paneer, Chapati, Salad).
- The items are always queried and displayed together with the parent meal session.
- Embedding eliminates expensive `$lookup` (JOIN) operations in real-time queries and guarantees document-level ACID atomicity.

#### Q5: When would you choose Referencing over Embedding in MongoDB?
**Answer:**
Referencing is preferred when:
1. Relationships are **1:Many** or **1:Millions** (e.g., Student to Attendance Logs), where embedding would exceed MongoDB's **16 MB BSON document size limit**.
2. Child documents are frequently updated independently of the parent.
3. Multiple unrelated parent documents reference the exact same child entity (Many-to-Many).

---

### Section B: Schema Validation & Data Integrity

#### Q6: How can MongoDB be "schema-less" if your project uses strict `$jsonSchema` validation?
**Answer:**
MongoDB is "schema-flexible" rather than strictly schema-less. By default, it allows any document structure. However, production enterprise applications require data integrity. MongoDB provides `$jsonSchema` validation configured via `collMod` or collection creation. It enforces data types, required fields, numeric bounds, and regex patterns at the database engine level upon every `insert` and `update`, giving us the flexibility of JSON with the integrity of an RDBMS.

#### Q7: What happens when a document violates your `$jsonSchema` validation?
**Answer:**
MongoDB immediately aborts the write operation with a `WriteError` (error code 121: `DocumentValidationFailure`) and returns a detailed failure report specifying which field or constraint failed (e.g., negative leftover, invalid meal type). In Python, PyMongo catches this as a `pymongo.errors.WriteError`.

#### Q8: What domain rules did you implement beyond `$jsonSchema`?
**Answer:**
In [database/validators.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/database/validators.py), we implemented application-level domain constraints:
1. **Leftover Invariant:** `total_prepared_kg >= total_leftover_kg` (leftovers cannot physically exceed total food cooked).
2. **Capacity Bounds:** `expected_attendance <= config.MESS_CAPACITY (1200)`.
3. **Itemized Sum Invariant:** Sum of individual dish preparation weights must equal the parent `total_prepared_kg` within a 1.0 kg tolerance.

---

### Section C: Indexing & Query Optimization

#### Q9: What indexes did you build and why?
**Answer:**
1. **Unique Index on `meal_id`:** Prevents accidental duplicate meal record insertions.
2. **Compound Unique Index on `[("meal_date", 1), ("meal_type", 1)]`:** Enforces the business rule that only one session of Breakfast, Lunch, Snacks, or Dinner can exist per calendar date.
3. **Single-Field B-Tree Index on `meal_date`:** Accelerates time-series range filtering (`$gte`, `$lte`).
4. **Multikey Index on `menu_items.item_name`:** Enables fast lookups of specific dishes embedded inside arrays without full collection scans.

#### Q10: What is a Multikey Index in MongoDB?
**Answer:**
When an index is created on an array field (such as `menu_items.item_name`), MongoDB creates a **Multikey Index**. It creates an index entry for every individual element in the array. This allows queries searching for meals containing `"Jeera Rice"` to use the B-tree index directly rather than scanning the entire collection.

#### Q11: How do you verify if a query uses an index in MongoDB?
**Answer:**
By chaining the `.explain("executionStats")` method in the MongoDB shell. We examine:
- `winningPlan.stage`: Should be `IXSCAN` (Index Scan) followed by `FETCH`, NOT `COLLSCAN` (Collection Scan).
- `totalDocsExamined` vs `nReturned`: Ideally, the ratio should be 1:1.

---

### Section D: Aggregation Pipelines

#### Q12: Explain how `$unwind` works in Aggregation 3 (Top Wasted Food Items).
**Answer:**
Each meal document contains an array `menu_items` with 3 to 5 dishes. The `$unwind` stage deconstructs this array: if a meal document has 4 items, `$unwind` emits 4 separate documents, each containing a single dish object in place of the array, while preserving the parent document's fields. This allows subsequent `$group` stages to aggregate metrics across individual dishes.

#### Q13: What is the purpose of `$switch` in Aggregation 4?
**Answer:**
The `$switch` operator functions as a multi-branch conditional (`if-elif-else`) inside a `$project` stage. We used it to bin continuous attendance counts into discrete operational bands:
- Case 1: `actual_attendance < 500` $\rightarrow$ "Low Attendance (< 500)"
- Case 2: `actual_attendance <= 800` $\rightarrow$ "Moderate Attendance (500-800)"
- Default: "High Attendance (> 800)"  
This allowed subsequent grouping to analyze waste patterns by attendance volume.

#### Q14: Why do you run aggregations in MongoDB instead of fetching data and using Pandas?
**Answer:**
Running aggregations in MongoDB:
1. **Minimizes Network Transfer:** Instead of transmitting 1,500 documents (several megabytes of JSON) over the network, MongoDB processes the data server-side and transmits only the final 4 grouped summary rows.
2. **C++ Native Speed:** MongoDB's aggregation engine is implemented in compiled C++ with optimized pipeline streaming.
3. **Scalability:** As the database grows to hundreds of thousands of records, fetching everything into Python memory would cause MemoryError crashes.

---

### Section E: Machine Learning & Benchmarking

#### Q15: What is "data leakage" in machine learning, and how did you prevent it?
**Answer:**
Data leakage occurs when information from outside the training dataset or post-event information is inadvertently included in model features during training, resulting in artificially inflated performance that fails in production.  
In our mess forecasting task:
- Post-meal variables like `actual_attendance` or actual diner counts **do not exist** when the kitchen prepares food 4 hours before the meal.
- Including `actual_attendance` would be severe target leakage.
- We strictly restricted features to **pre-meal operational data**: `expected_attendance`, `buffer_percentage`, `total_prepared_kg`, scheduled `meal_type`, date/calendar flags, and forecast weather.

#### Q16: Why did you compare Random Forest Regressor with Decision Tree Regressor?
**Answer:**
To demonstrate the academic and practical benefits of **ensemble learning** over single-tree heuristics:
- **Decision Tree (CART):** Creates a single decision tree (depth 6). It is fast and interpretable but suffers from high variance and sensitivity to training data noise ($MAE = 14.645\text{ kg}$).
- **Random Forest:** Builds an ensemble of 100 decorrelated trees using bootstrap aggregation (bagging) and random feature subsampling. By averaging predictions across 100 trees, it mitigates individual tree variance, resulting in superior generalization ($MAE = 14.229\text{ kg}$, a **+7.68% improvement** over baseline).

#### Q17: What metrics did you use to evaluate your regression models?
**Answer:**
1. **Mean Absolute Error (MAE):** $\frac{1}{n} \sum |y_i - \hat{y}_i|$. Gives the average forecasting error directly in physical units (kilograms).
2. **Root Mean Squared Error (RMSE):** $\sqrt{\frac{1}{n} \sum (y_i - \hat{y}_i)^2}$. Penalizes large outlier errors more heavily.
3. **Coefficient of Determination ($R^2$):** Proportion of variance in leftover kilograms explained by operational features ($R^2 \approx 0.4959$ for Random Forest).

#### Q18: Why is Recall prioritized over Precision for the High-Waste Classifier?
**Answer:**
The classifier predicts whether leftover food will exceed a critical threshold (>35 kg):
- A **False Positive** (predicting high waste when it was normal) causes the kitchen to prepare slightly more conservative buffers—minimal negative consequence.
- A **False Negative** (predicting normal when severe surplus actually occurs) results in 50+ kg of food ending up in the garbage—high financial and environmental cost.  
Therefore, we prioritized **Recall (88.97%)** by utilizing balanced class weights to ensure 9 out of 10 severe waste events are caught proactively.

---

### Section F: Faculty "Trap" Questions & Defense Strategies

#### Q19: "Why is your $R^2$ score ~0.50? Isn't an $R^2$ of 0.90 better?"
**Answer:**
"In human behavioral systems like university dining halls, food intake varies based on unobservable human factors (e.g., students ordering outside food, skipping breakfast after late-night study, taste preference variations). Models reporting $R^2 > 0.90$ in food waste literature almost always suffer from **data leakage**—such as using `actual_attendance` or post-meal consumption as input features. In a true, zero-leakage operational setting using only pre-meal inputs, an $R^2 \approx 0.50$ with a low MAE of 14.2 kg represents a realistic, robust, and deployable model."

#### Q20: "What happens if MongoDB goes down while the Streamlit dashboard is running?"
**Answer:**
"Our `database/connection.py` wraps connection retrieval in a try-except block with a 5000 ms timeout. If the database is unreachable, the application gracefully displays an informative Streamlit warning banner informing the manager that live database operations are offline, while retaining cached predictions and offering a retry button rather than crashing with an unhandled exception."

#### Q21: "Can a predicted leftover value be negative or exceed prepared food?"
**Answer:**
"No. Standard linear regression or unrestricted tree algorithms can theoretically output negative values. In [ml/predict.py](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/ml/predict.py), we enforce strict physical bounding:
$$\hat{y}_{\text{bounded}} = \max(0.0, \min(\hat{y}_{\text{raw}}, \text{total\_prepared\_kg}))$$
This mathematically guarantees that predicted leftovers are always non-negative and never exceed the total food cooked."

#### Q22: "How does your system save money in practice?"
**Answer:**
"When the manager enters the planned meal parameters, the system outputs the forecasted leftover (e.g., 48 kg, High Waste Risk). The system immediately recommends reducing the kitchen buffer from 15% to 5% (saving ~30 kg of food). At ₹45/kg, this saves ₹1,350 on a single meal session. Over a month of 120 meal sessions, this translates to over ₹1,00,000 in direct grocery and raw material savings."
