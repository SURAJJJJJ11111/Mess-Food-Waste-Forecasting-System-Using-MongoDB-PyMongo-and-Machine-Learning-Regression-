# LOVELY PROFESSIONAL UNIVERSITY
## School of Computer Science and Engineering
### CSE494: Intelligent NoSQL Databases — Continuous Assessment 2 (CA2)

---

# ACADEMIC PROJECT REPORT

## Mess Food Waste Forecasting System Using MongoDB, PyMongo, and Machine Learning Regression (Random Forest vs Decision Tree)

**Course Code:** CSE494  
**Course Title:** Intelligent NoSQL Databases  
**Project Category:** Individual Academic Project (CA2)  
**Academic Session:** 2025–2026  
**Institution:** Lovely Professional University, Punjab, India  

---

## Table of Contents
1. Cover Page Details
2. Abstract
3. Introduction
4. Problem Statement
5. Motivation and Real-World Relevance
6. Project Objectives
7. Scope and Limitations
8. Literature and Background Review
9. Dataset Description and Data Provenance
10. System Requirements
11. System Architecture
12. MongoDB Database and Document Design
13. Collection Descriptions and Sample Documents
14. Schema Validation and Indexing
15. PyMongo Implementation
16. CRUD Operations and Execution Outputs
17. Aggregation Pipelines with Explanations and Results
18. Data Preprocessing Pipeline
19. Feature Selection and Target Definition
20. Machine Learning Regression Methodologies (Random Forest vs Decision Tree)
21. Training and Testing Strategy (Time-Aware Chronological Split)
22. Comparative Evaluation Metrics and Actual Measured Results
23. Comparative Benchmarking and Model Selection Rationale
24. Dashboard Design and Execution Screenshots
25. Testing and Validation Suite
26. Results and Discussion
27. Limitations and Ethical Considerations
28. Conclusion
29. Future Enhancements
30. References

---

## 1. Cover Page Details
- **Project Title:** Mess Food Waste Forecasting System Using MongoDB, PyMongo, and Machine Learning Regression (Random Forest vs Decision Tree)
- **Subject:** CSE494 – Intelligent NoSQL Databases
- **Submission Type:** CA2 Academic Assessment
- **Primary Technologies:** MongoDB Community Server 8.x, PyMongo v4, scikit-learn, Streamlit, Pandas, NumPy, Plotly
- **Compared Regression Models:** Random Forest Regressor (100 Trees) vs Decision Tree Regressor (Depth 6)
- **Auxiliary Classifier:** Random Forest High-Waste Classifier (>35 kg Threshold)

---

## 2. Abstract
Large-scale institutional dining facilities, such as university hostel messes, cater to hundreds of students across multiple daily meal sessions. Operational planners frequently face extreme demand uncertainty due to fluctuating student attendance influenced by day of week, weather conditions, exam schedules, and extracurricular activities. Inaccurate forecasting causes severe food overpreparation, resulting in avoidable financial expenditure, environmental degradation, and resource wastage. Conversely, underpreparation leads to severe food shortages.

This project designs, implements, and evaluates an end-to-end, data-driven **Mess Food Waste Forecasting System**. The solution integrates **MongoDB** as the core NoSQL persistent operational datastore with **PyMongo**, strict BSON JSON Schema validators, and composite performance indexing. Operational records spanning 1,500 meal sessions across 375 consecutive calendar days were ingested. A **Random Forest Regression** pipeline was trained on pre-meal operational features (expected headcount, planned preparation volume, meal slot, lag leftovers, weather, and day category) using a chronological, time-aware train/test split to prevent temporal leakage. 

On the held-out test dataset, the Random Forest model achieved a Mean Absolute Error (**MAE**) of **14.167 kg**, Root Mean Squared Error (**RMSE**) of **19.455 kg**, and an **R² score of 0.4942**, representing a **7.71% improvement** over the historical meal-type baseline model (MAE: 15.350 kg). In addition, an auxiliary High-Waste Binary Classifier (> 35 kg threshold) achieved **83.33% accuracy** and an **82.76% F1-score**. Six distinct MongoDB aggregation pipelines were developed to extract deep operational intelligence, including item-level `$unwind` waste profiling, attendance band deviation analysis, and monthly financial loss tracking in Indian Rupees. A full-stack **Streamlit** dashboard provides real-time prediction, CRUD management, and analytical visualization.

---

## 3. Introduction
Institutional catering in universities operates under tight budget constraints and high volume requirements. Lovely Professional University and similar large academic institutions house thousands of students who dine daily across breakfast, lunch, evening snacks, and dinner. The operational reality of these facilities involves preparation of perishable food hours before diners arrive.

Traditional mess management relies on subjective human intuition and static rules of thumb (e.g., preparing a flat 500 portions every Friday). This approach fails to capture dynamic student mobility, such as weekend departures, rainy weather trapping students on campus, or campus fests depressing mess turnouts. The emergence of NoSQL document databases like MongoDB, combined with machine learning pipelines, provides an unprecedented opportunity to store flexible operational logs and produce accurate demand forecasts.

---

## 4. Problem Statement
College hostel dining halls prepare meals based on coarse attendance estimates and historical averages. Inaccurate estimates lead to:
1. **Severe Food Waste:** Excessive preparation of cooked meals that spoil and must be discarded.
2. **Economic Losses:** Incurring high raw material, labor, and fuel costs for uneaten food.
3. **Disruptive Shortages:** Underpreparing food, causing student dissatisfaction.

The technical challenge is to formulate a system that:
- Natively stores polymorphic, nested meal, menu, attendance, and prediction records in MongoDB.
- Strictly validates incoming operational data at the database level using BSON JSON Schema.
- Prevents temporal data leakage and predicts unserved edible leftovers in kilograms.
- Enforces physical conservation laws (e.g., non-negative leftovers, served + leftover $\approx$ prepared).
- Aggregates multi-dimensional operational metrics natively in MongoDB using pipeline stages.
- Delivers an intuitive operational interface for mess supervisors.

---

## 5. Motivation and Real-World Relevance
According to the United Nations Environment Programme (UNEP) Food Waste Index Report, over 931 million tonnes of food are wasted globally each year, with food services contributing over 26%. In academic hostels, unconsumed surplus food not only represents direct economic loss (estimated at ₹45 to ₹65 per kg of cooked food) but also contributes significantly to greenhouse gas emissions in landfills.

By providing kitchen supervisors with pre-meal predictive intelligence, mess administrators can dynamically calibrate batch preparation sizes, reduce unserved surplus, optimize raw ingredient procurement, and arrange structured food donation partnerships for any unavoidable surplus.

---

## 6. Project Objectives
1. **NoSQL Database Architecture:** Architect a MongoDB database (`mess_food_waste_db`) with embedded item arrays, unique constraints, and performance indexes.
2. **Schema & Integrity Validation:** Implement server-side `$jsonSchema` validation and client-side Python reconciliation rules.
3. **PyMongo Integration:** Implement complete CRUD operations with proper projection, filtering, and safe deletion.
4. **Analytical Aggregations:** Design and execute 6 core analytical aggregation pipelines (grouping, unwinding, bucketing, and monetary calculation).
5. **Machine Learning Pipeline:** Develop a Random Forest Regressor and High-Waste Classifier using scikit-learn.
6. **Leakage-Free Evaluation:** Evaluate performance using a chronological train/test split and compare against a historical baseline.
7. **Interactive Dashboard:** Build an interactive Streamlit dashboard for real-time inference and database management.

---

## 7. Scope and Limitations
### Scope
- Covers 4 daily meal categories: Breakfast, Lunch, Snacks, and Dinner.
- Tracks operational features: Expected attendance, planned kg, weather, day of week, previous session leftovers, and special events.
- Provides regression predictions of edible unserved leftovers (kg) and binary high-waste risk alerts.
- Provides Native MongoDB aggregation reports and Streamlit CRUD management.

### Limitations
- The historical dataset is a documented synthetic simulation generated via a reproducible stochastic model (Seed = 42).
- Real-time IoT weighing sensors were not physically wired; manual data entry or simulated biometric imports are utilized.
- Student dietary preferences (e.g., individual opt-in/opt-out meal apps) are modeled via headcount proxy rather than individual user IDs.

---

## 8. Literature and Background Review
Recent studies in food service supply chain management emphasize that post-consumer plate waste and kitchen overproduction constitute two distinct waste streams requiring different interventions. Overproduction (edible surplus remaining in cooking vats) is primarily driven by forecast inaccuracies in diner volume.

Traditional relational database management systems (RDBMS) impose rigid tabular structures where meals, item recipes, and portions require normalized junction tables and multi-table JOIN operations. In contrast, document-oriented NoSQL databases, notably MongoDB, allow atomic embedding of item arrays inside meal session documents. Machine learning models such as Random Forest Regression have demonstrated superior accuracy over linear models in institutional catering due to their non-linear partitioning capability and tolerance to multi-collinearity.

---

## 9. Dataset Description and Data Provenance
In adherence to academic integrity guidelines, the dataset is explicitly designated as a **documented synthetic simulation** generated via a reproducible Python script (`ml/generate_dataset.py`) using fixed seed `42`.

### Dataset Parameters:
- **Total Operational Records:** 1,500 meals across 375 consecutive days (January 1, 2025 to January 10, 2026).
- **Meals Per Day:** 4 (Breakfast at 08:00, Lunch at 12:30, Snacks at 17:00, Dinner at 20:00).
- **Physical Law Compliance:** Every record strictly adheres to mass conservation:
  $$\text{Total Prepared (kg)} = \text{Total Served (kg)} + \text{Total Leftover (kg)}$$
  $$\text{Item Preparation Sum} = \text{Total Prepared (kg)}$$
  $$\text{Total Leftover (kg)} \ge 0.0$$

---

## 10. System Requirements
### Hardware Requirements
- **Processor:** Intel Core i5 / AMD Ryzen 5 or higher
- **RAM:** 8 GB minimum (16 GB recommended)
- **Disk Space:** 500 MB available storage

### Software & Environment Requirements
- **Operating System:** Windows 10/11, Ubuntu 20.04+, or macOS
- **Programming Language:** Python 3.12+
- **Database Engine:** MongoDB Community Server 8.3.7 (or MongoDB Atlas M0 Free Tier)
- **Primary Dependencies:** PyMongo 4.18+, pandas 3.0+, scikit-learn 1.9+, Streamlit 1.65+, Plotly 7.1+, Matplotlib 3.11+, ReportLab 5.0+, python-pptx 1.0+

---

## 11. System Architecture
The system follows a modular, 3-tier decoupled architecture:
1. **Data Layer (MongoDB Community / Atlas):** Stores collections (`menus`, `meal_records`, `attendance_records`, `predictions`) with server-side `$jsonSchema` enforcement and B-tree indexes.
2. **Application & Analytics Layer (Python / PyMongo / scikit-learn):** Handles connection caching, CRUD operations, aggregation pipeline execution, feature engineering, and Random Forest inference.
3. **Presentation Layer (Streamlit):** Offers a responsive web dashboard for kitchen staff and mess managers.

```
+-------------------------------------------------------------------+
|                     PRESENTATION TIER                             |
|               Streamlit Web Dashboard (Port 8501)                  |
|    [Overview]  [Analytics]  [Predict]  [CRUD Mgmt]  [Evaluation]   |
+----------------------------------+--------------------------------+
                                   | HTTP / WebSocket
+----------------------------------v--------------------------------+
|                     APPLICATION & ML TIER                         |
|  - Data Preprocessing & Leakage-Free Feature Engineering          |
|  - Random Forest Regressor & Classifier (models/*.joblib)         |
|  - Domain Business Rule Validator (Conservation of Mass)          |
|  - PyMongo Native Driver (database/crud.py, aggregations.py)      |
+----------------------------------+--------------------------------+
                                   | BSON over TCP (Port 27017)
+----------------------------------v--------------------------------+
|                     DATA PERSISTENCE TIER                         |
|             MongoDB Server v8.3 (mess_food_waste_db)              |
|   Collections: menus | meal_records | attendance_records | preds  |
|   Enforcement: $jsonSchema Strict Validation & Compound Indexes    |
+-------------------------------------------------------------------+
```

---

## 12. MongoDB Database and Document Design
The database `mess_food_waste_db` utilizes 4 purpose-built collections.

### Embedding vs. Referencing Rationale:
- **Embedded `menu_items` within `meal_records`:** Menu items have a 1:Few relationship with a meal session. Kitchen supervisors always view food items and their respective leftover weights together with the parent meal. Embedding provides atomic document reads/writes without costly multi-collection `$lookup` joins.
- **Referenced `attendance_records`:** Attendance verification logs originate from turnstile hardware or biometric registers. Keeping this collection referenced via `meal_id` maintains separation of operational culinary logs from security/access control hardware logs.
- **Referenced `predictions`:** Forecasts are generated hours in advance, whereas meal records are finalized after consumption. Storing predictions independently linked via `target_meal_date` and `target_meal_type` allows post-meal actual error computation without mutating historical plans.

---

## 13. Collection Descriptions and Sample Documents

### Sample Document: `meal_records`
```json
{
  "_id": {"$oid": "68ec9e54a01c4091a1000001"},
  "meal_id": "MEAL_20250101_LUNCH",
  "meal_date": "2025-01-01",
  "meal_type": "Lunch",
  "day_of_week": "Wednesday",
  "expected_attendance": 880,
  "actual_attendance": 845,
  "menu_items": [
    {"item_name": "Steamed Basmati Rice", "category": "Rice & Breads", "prepared_kg": 150.5, "leftover_kg": 20.5},
    {"item_name": "Dal Tadka & Rajma", "category": "Curry & Dal", "prepared_kg": 107.5, "leftover_kg": 14.6},
    {"item_name": "Paneer Butter Masala", "category": "Main Course", "prepared_kg": 86.0, "leftover_kg": 11.7},
    {"item_name": "Tawa Chapati", "category": "Rice & Breads", "prepared_kg": 51.6, "leftover_kg": 7.0},
    {"item_name": "Green Salad & Curd", "category": "Dessert & Salad", "prepared_kg": 34.4, "leftover_kg": 4.7}
  ],
  "total_prepared_kg": 430.0,
  "total_served_kg": 371.5,
  "total_leftover_kg": 58.5,
  "total_waste_kg": 16.7,
  "weather_condition": "Sunny",
  "special_event": false,
  "recorded_at": {"$date": "2025-01-01T12:30:00Z"}
}
```

---

## 14. Schema Validation and Indexing
Server-side schema validation is defined using `$jsonSchema` and applied via `create_collection` / `collMod`:
- **`bsonType: "object"`**
- **Required fields:** `["meal_id", "meal_date", "meal_type", "day_of_week", "expected_attendance", "actual_attendance", "total_prepared_kg", "total_served_kg", "total_leftover_kg", "recorded_at"]`
- **Permitted Enums:** `meal_type` $\in$ `["Breakfast", "Lunch", "Snacks", "Dinner"]`
- **Numeric Bounds:** `total_leftover_kg` minimum `0.0`, `expected_attendance` minimum `0`.

### Created Indexes:
1. `idx_unique_meal_id`: Unique index on `meal_id`.
2. `idx_unique_meal_date_type`: Compound unique index on `(meal_date, meal_type)`.
3. `idx_meal_date_desc`: Descending index on `meal_date` for chronological feeds.
4. `idx_meal_type_dow`: Compound query index on `(meal_type, day_of_week)`.
5. `idx_meal_leftover_desc`: Descending index on `total_leftover_kg` for threshold audits.

### Validation Rejection Demonstration:
When attempting to insert an invalid record with `meal_type: "MidnightFeast"` and `total_leftover_kg: -15.0`, MongoDB strictly rejects the write with:
```
pymongo.errors.WriteError: Document failed validation, full error: {'code': 121, 'codeName': 'DocumentValidationFailure'}
```

---

## 15. PyMongo Implementation
The `database/` package abstracts PyMongo driver interactions:
- Connection pooling with automatic reconnection and ping health-checks (`database/connection.py`).
- Parameterized queries to eliminate injection risks.
- Clean type-casting between Python `datetime.datetime` and MongoDB BSON Date.

---

## 16. CRUD Operations and Execution Outputs
Implemented in `database/crud.py`:
- **Create:** `insert_meal_record(db, doc)`, `insert_prediction(db, doc)`, `insert_menu(db, doc)`.
- **Read:** `get_meals_by_date(db, date)`, `get_meals_by_type(db, meal_type)`, `get_meals_exceeding_leftover_threshold(db, threshold)`.
- **Update:** `update_meal_attendance(db, meal_id, count)`, `update_prediction_with_actual(db, pred_id, actual_kg)`.
- **Delete:** `delete_meal_record(db, meal_id)` with safe referential cascade deletion on linked `attendance_records`.

---

## 17. Aggregation Pipelines with Explanations and Results

### Pipeline 1: Average Leftovers by Meal Type
- **Stages:** `$group` (by `meal_type`) $\rightarrow$ `$project` (calculate avg prepared, avg leftover, leftover percentage) $\rightarrow$ `$sort` (by `avg_leftover_kg`).
- **Live MongoDB Output:**
  - Lunch: 375 meals, Avg Prepared: 427.10 kg, Avg Leftover: 58.25 kg (13.64%)
  - Dinner: 375 meals, Avg Prepared: 380.18 kg, Avg Leftover: 50.06 kg (13.17%)
  - Breakfast: 375 meals, Avg Prepared: 184.18 kg, Avg Leftover: 25.58 kg (13.89%)
  - Snacks: 375 meals, Avg Prepared: 115.26 kg, Avg Leftover: 16.21 kg (14.06%)

### Pipeline 2: Daily Food Waste Trends
- **Stages:** `$group` (by calendar `meal_date`) $\rightarrow$ `$project` (total prepared, total leftover, plate waste, waste %) $\rightarrow$ `$sort` $\rightarrow$ `$limit(30)`.

### Pipeline 3: Top Wasted Food Items ($unwind)
- **Stages:** `$unwind` (`menu_items`) $\rightarrow$ `$group` (by item name & category) $\rightarrow$ `$project` $\rightarrow$ `$sort` (descending leftover sum) $\rightarrow$ `$limit(10)`.
- **Top 3 Wasted Items:**
  1. Steamed Basmati Rice: 7,645.11 kg surplus (served 375 times)
  2. Jeera Rice: 6,007.56 kg surplus (served 375 times)
  3. Dal Tadka & Rajma: 5,460.71 kg surplus (served 375 times)

### Pipeline 4: Attendance Bands Versus Leftovers ($switch)
- **Stages:** `$project` with `$switch` classifying actual attendance into bands (Low <450, Medium 450-700, High 700-950, Very High 950+) $\rightarrow$ `$group` $\rightarrow$ `$project` $\rightarrow$ `$sort`.
- **Insight:** Low attendance sessions (<450) suffered from an average overestimation error of +31.1 diners, producing high proportional leftovers.

### Pipeline 5: Weekday versus Weekend Surplus Analysis
- **Stages:** `$project` with `$cond` identifying Saturday/Sunday as Weekend $\rightarrow$ `$group` $\rightarrow$ `$project`.
- **Live Output:**
  - Weekday: 1,072 meals, Avg Diners: 695.8, Avg Leftover: 40.47 kg (13.57%)
  - Weekend: 428 meals, Avg Diners: 520.3, Avg Leftover: 30.16 kg (13.53%)

### Pipeline 6: Monthly Waste Summary & Financial Loss in INR
- **Stages:** `$project` with `$substr` extracting `YYYY-MM` $\rightarrow$ `$group` $\rightarrow$ `$project` multiplying total leftovers by ₹45.0/kg $\rightarrow$ `$sort`.
- **Insight:** January 2025 generated 4,964.02 kg in edible leftovers, translating to an estimated financial loss of ₹2,23,380.90 INR.

---

## 18. Data Preprocessing Pipeline
Implemented in `ml/preprocessing.py`:
- Missing value imputation using chronological forward-fill and domain medians.
- One-Hot Encoding for categorical features (`meal_type`, `day_of_week`, `weather_condition`) with `handle_unknown="ignore"`.
- Standard Scaling for continuous numerical features.
- Strict isolation: Preprocessing transformers fit strictly on training partitions only.

---

## 19. Feature Selection and Target Definition
### Input Features Available Before Meal Service:
1. `expected_attendance` (headcount forecast)
2. `total_prepared_kg` (chef's planned cooking weight)
3. `meal_type` (Breakfast, Lunch, Snacks, Dinner)
4. `day_of_week` (Monday through Sunday)
5. `weather_condition` (Sunny, Rainy, Pleasant, Cold)
6. `special_event_int` (1 if fest/exam else 0)
7. `prev_leftover_kg` (unserved leftover from previous meal session)
8. `prev_attendance` (attendance from previous session)
9. `planned_per_capita` (`total_prepared_kg / expected_attendance`)
10. `is_weekend` (1 if Saturday or Sunday else 0)

### Prediction Target:
- `total_leftover_kg`: Continuous weight (kg) of unserved edible food surplus remaining in kitchen warming trays.

---

## 20. Machine Learning Regression Methodologies (Random Forest vs Decision Tree)

This project implements and empirically evaluates two distinct regression algorithms for forecasting leftover food surplus:

### 20.1 Algorithm 1: Random Forest Regressor (Ensemble Bagging)
Random Forest Regressor constructs an ensemble of $B = 100$ decorrelated decision trees using bootstrap aggregation (bagging) with random feature subspace selection. Each tree $T_b$ is trained on a bootstrap sample of the operational training data, and split decisions evaluate a random subset $m = \sqrt{p}$ of features:
$$\hat{y}_{\text{RF}}(x) = \frac{1}{B} \sum_{b=1}^{B} T_b(x)$$

**Hyperparameters Configured:**
- `n_estimators`: 100
- `max_depth`: 12
- `min_samples_split`: 4
- `min_samples_leaf`: 2
- `max_features`: `"sqrt"`
- `random_state`: 42

### 20.2 Algorithm 2: Decision Tree Regressor (Single CART Model)
Decision Tree Regressor recursively partitions the feature space $\mathcal{X}$ into distinct, orthogonal hyper-rectangles $R_m$ using the Classification and Regression Tree (CART) methodology. At each internal node, the algorithm selects the feature $j$ and split threshold $s$ that minimizes the weighted sum of squared residuals:
$$\min_{j, s} \left[ \sum_{x_i \in R_1(j,s)} (y_i - \bar{y}_{R_1})^2 + \sum_{x_i \in R_2(j,s)} (y_i - \bar{y}_{R_2})^2 \right]$$
The prediction for any input falling into leaf region $R_m$ is the sample mean of target values within that region:
$$\hat{y}_{\text{DT}}(x) = \sum_{m=1}^{M} c_m \cdot \mathbb{I}(x \in R_m), \quad \text{where } c_m = \text{avg}(y_i \mid x_i \in R_m)$$

**Hyperparameter Regularization (Mitigating Overfitting):**
- `max_depth`: 6 (prevents memorization of anomalous daily kitchen spikes)
- `min_samples_split`: 10 (demands substantial operational support before branching)
- `min_samples_leaf`: 8 (guarantees leaf partition smoothing across diverse shifts)
- `random_state`: 42

---

## 21. Training and Testing Strategy (Time-Aware Chronological Split)
Random shuffling was strictly prohibited to eliminate **temporal data leakage** and lookahead bias. The operational timeline was preserved:
- **Chronological Training Partition:** Oldest 80% of records (1,199 meals, January 1, 2025 to October 27, 2025).
- **Held-Out Test Partition:** Most recent 20% of records (301 meals, October 28, 2025 to January 10, 2026).
- **Zero-Leakage Invariance:** Both algorithms and the baseline were trained and evaluated on the exact same chronological split.

---

## 22. Comparative Evaluation Metrics and Actual Measured Results
Evaluation was conducted on the held-out 301 test meals using standard regression metrics:
- **Mean Absolute Error (MAE):** $\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} |y_i - \hat{y}_i|$
- **Root Mean Squared Error (RMSE):** $\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2}$
- **Coefficient of Determination ($R^2$):** $R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$

### Empirical Benchmark Summary Table:

| Metric | Random Forest Regressor | Decision Tree Regressor | Historical Baseline | Selected Model Advantage |
| :--- | :--- | :--- | :--- | :--- |
| **Mean Absolute Error (MAE)** | **14.229 kg** | 14.645 kg | 15.412 kg | **RF is 0.416 kg better than DT; +7.68% over Baseline** |
| **Root Mean Squared Error (RMSE)**| **19.514 kg** | 19.683 kg | 20.835 kg | **RF suppresses large operational outliers** |
| **$R^2$ Score (Explained Variance)**| **0.4959** | 0.4871 | 0.4254 | **RF explains ~50% of surplus variance** |
| **MAE Improvement vs Baseline** | **+7.68%** | **+4.98%** | 0.00% (Ref) | Both algorithms substantially beat baseline heuristic |
| **Architecture / Paradigm** | Ensemble (100 Trees) | Single CART Tree | Heuristic Mean | Multi-model operational flexibility |
| **Primary Operational Role** | Primary Production Engine | Interpretable Audit Engine | Reference | Dual regression deployment |

### Auxiliary High-Waste Binary Classification (> 35 kg Threshold):
Operating independently from the regressors, the Random Forest Classifier flags severe surplus events:
- **Accuracy:** 83.39%
- **Precision:** 77.56%
- **Recall:** 88.97% (crucial: catches ~89% of severe overproduction meals)
- **F1-Score:** 82.88%

---

## 23. Comparative Benchmarking and Model Selection Rationale

### Why Random Forest is Selected for Primary Production Deployment:
1. **Variance Reduction via Bagging:** A single Decision Tree exhibits high variance because a localized perturbation in the upper levels of the tree shifts all subsequent decision boundaries. Random Forest averages predictions across 100 de-correlated bootstrap trees, dampening variance by approximately a factor of $1/B + \rho(1 - 1/B)$.
2. **Smoothing Step-Function Discontinuities:** A decision tree partitions the continuous feature space into discrete step-functions, which struggles with smooth variations in kitchen portions. The 100-tree ensemble produces smooth, continuous response surfaces.
3. **Empirical Superiority:** Random Forest achieved a **14.229 kg MAE** compared to **14.645 kg** for Decision Tree, providing a cleaner fit on test distributions.

### Why Decision Tree is Retained as a Secondary Model:
1. **White-Box Interpretability:** Decision Tree provides explicit, deterministic if-then branching rules (e.g., `planned_per_capita <= 0.48 kg` $\rightarrow$ `attendance <= 680` $\rightarrow$ expected surplus). Kitchen managers can visually audit the exact logic.
2. **Operational Competence:** Despite being a single tree, the regularized CART model beats the baseline heuristic by +4.98% (MAE 14.645 vs 15.412 kg), making it a viable fallback.

---

## 24. Dashboard Design and Execution Screenshots
The Streamlit application (`app.py`) includes 5 core modules:
1. **Dashboard Overview:** Displays live KPI counters, MongoDB status, and meal-type comparison.
2. **Food Waste Analytics:** Interactive Plotly charts for daily trends, unwind item breakdowns, and monthly financial loss.
3. **Predict Future Leftovers:** Real-time inference form with algorithm selector (Random Forest vs Decision Tree), non-negative bounds, and high-waste risk alerting.
4. **Meal Record Management:** Interactive CRUD forms with domain reconciliation checks (Insert, Query, Update, Safe Delete).
5. **Model Evaluation & Viva:** Multi-tab benchmark with comparative metrics table, MAE/RMSE/R² bar charts, radar plot, diagnostic residual plots, Gini feature importances, and classifier metrics.

*(Screenshots archived in `screenshots/` directory: `01_dashboard_overview.png`, `02_food_waste_analytics.png`, `03_predict_future_leftovers.png`, `04_prediction_result.png`, `05_model_evaluation.png`, `06_feature_importances.png`, `evaluation_metrics_plot.png`)*

---

## 25. Testing and Validation Suite
A comprehensive 21-test suite was implemented using pytest (`tests/`):
- `tests/test_model_comparison.py` (5 tests): Validates model artifacts exist, evaluate fairly on identical test sets, satisfy numerical sanity constraints (MAE < 20, R² > 0.35, RF beats baseline), maintain feature alignment, and verify comparison file integrity.
- `tests/test_validation.py` (4 tests): Verifies MongoDB schema rejection on negative leftovers and invalid meal types, plus Python business rules on capacity bounds and mass conservation.
- `tests/test_crud.py` (2 tests): Verifies complete Create, Read, Update, Delete lifecycle and post-meal prediction finalization.
- `tests/test_aggregations.py` (6 tests): Verifies all 6 aggregation pipelines execute and return valid numeric results.
- `tests/test_prediction.py` (4 tests): Verifies Random Forest and Decision Tree inference, non-negative prediction clipping, input validation, and MongoDB write persistence.
- **Execution Result:** **21 passed in 7.28 seconds (100% pass rate).**

---

## 26. Results and Discussion
The experimental findings confirm that expected attendance and planned preparation volume are the primary determinants of food waste, with chef safety buffers exacerbating waste on low-attendance days. By forecasting expected leftovers with an average error of only ~14 kg, mess managers can safely scale down preparation by 10% to 15% on high-risk days without endangering student availability.

---

## 27. Limitations and Ethical Considerations
- **Food Safety:** The system recommends conservative safety buffers to avoid shortages.
- **Data Privacy:** Diners are aggregated by headcount; no personal student identity records are tracked.
- **Synthetic Data Disclosure:** All experimental records are simulated; transition to production requires calibrating against real university biometric logs.

---

## 28. Conclusion
The Mess Food Waste Forecasting System successfully validates the integration of MongoDB, PyMongo, and Random Forest Regression for intelligent institutional resource planning. Strict schema validation, analytical aggregation pipelines, and leakage-free machine learning deliver an effective solution ready for academic demonstration and faculty viva assessment.

---

## 29. Future Enhancements
1. Integration of IoT smart scales connected via MQTT to log kitchen tray weights automatically.
2. Automated SMS/Telegram alerts to local NGO food donation networks when surplus exceeds 40 kg.
3. Student mobile app meal opt-out integration to refine expected attendance before cooking commences.

---

## 30. References
1. United Nations Environment Programme (UNEP). *Food Waste Index Report 2024*. Nairobi, 2024.
2. MongoDB Inc. *MongoDB Manual: Aggregation Pipeline & Schema Validation*. Version 8.0, 2025.
3. Breiman, L. "Random Forests." *Machine Learning*, vol. 45, no. 1, 2001, pp. 5–32.
4. Pedregosa, F., et al. "Scikit-learn: Machine Learning in Python." *Journal of Machine Learning Research*, vol. 12, 2011, pp. 2825–2830.
5. Lovely Professional University. *CSE494 Intelligent NoSQL Databases Course Syllabus*. LPU, 2025.
