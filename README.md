# Mess Food Waste Forecasting System Using MongoDB, PyMongo, and Machine Learning Regression (Random Forest vs Decision Tree)

**Course:** CSE494 – Intelligent NoSQL Databases (Continuous Assessment 2 - CA2)  
**Institution:** Lovely Professional University, Punjab, India  
**Technology Stack:** Python 3.12, MongoDB Community Server 8.x / Atlas, PyMongo v4, scikit-learn, Streamlit, Pandas, NumPy, Plotly, ReportLab, python-pptx  

---

## 1. Project Overview
Large college messes and hostel dining halls face significant food overproduction due to fluctuating student turnouts. This project implements a complete, data-driven food waste forecasting and operational management platform that integrates:
- **MongoDB** as the core NoSQL persistent datastore with embedded document structures, composite indexes, and strict `$jsonSchema` validation.
- **PyMongo** for atomic CRUD operations and analytical aggregation pipelines.
- **Dual Machine Learning Regression Benchmark:** Compares **Random Forest Regressor** (100 bootstrap trees) against **Decision Tree Regressor** (CART, regularized depth 6) to forecast edible unserved leftovers (in kilograms) using zero-leakage pre-meal operational features.
- **Auxiliary High-Waste Classifier:** Flags severe overproduction risk (>35 kg) with 88.97% recall.
- **Streamlit** multi-page interactive web dashboard featuring algorithm switching, real-time predictions, analytics, and operational CRUD management.

---

## 2. Directory Structure

```
mess-food-waste-forecasting/
├── app.py                          # Main Streamlit web application (5 pages, Theme Toggle)
├── config.py                       # Central configuration, dual model paths & comparison paths
├── requirements.txt                # Python library dependencies
├── .env.example                    # Example environment variable file
├── .env                            # Local environment configuration
├── README.md                       # Complete documentation and setup guide
├── queries.mongodb.js              # Native MongoDB shell / Compass queries & pipelines
├── presentation.pptx               # 12-slide PowerPoint presentation with comparative benchmark
│
├── database/                       # MongoDB database modules
│   ├── __init__.py
│   ├── connection.py               # Thread-safe MongoDB connection pooling
│   ├── setup.py                    # Schema validators & index initializers
│   ├── validators.py               # BSON JSON Schema & domain rule validators
│   ├── indexes.py                  # Unique and query performance indexes
│   ├── crud.py                     # PyMongo CRUD operations implementation
│   └── aggregations.py             # The 6 core analytical aggregation pipelines
│
├── ml/                             # Machine learning package
│   ├── __init__.py
│   ├── generate_dataset.py         # Documented synthetic dataset generator (Seed=42)
│   ├── preprocessing.py            # Leakage-free feature pipeline & time-aware split
│   ├── train_model.py              # Dual regression (RF + DT) & classifier training
│   ├── predict.py                  # Dual-algorithm inference workflow with non-negative bounds
│   └── evaluate.py                 # Comparative evaluation & 4-panel diagnostic chart generator
│
├── scripts/                        # Automation & demonstration scripts
│   ├── __init__.py
│   ├── seed_database.py            # Database bootstrapping (1,500 records)
│   └── run_aggregations.py         # Aggregation pipeline demonstration runner
│
├── tests/                          # Automated test suite (pytest - 21 tests)
│   ├── __init__.py
│   ├── test_model_comparison.py    # Dual model benchmark, fairness & sanity tests
│   ├── test_validation.py          # Schema rejection & domain rule tests
│   ├── test_crud.py                # End-to-end CRUD verification
│   ├── test_aggregations.py        # Pipeline execution tests
│   └── test_prediction.py          # Dual-algorithm inference bounds & persistence tests
│
├── data/                           # Dataset storage
│   ├── README.md                   # Dataset documentation & data dictionary
│   ├── historical_meal_records.csv
│   └── historical_meal_records.json
│
├── models/                         # Serialized machine learning models
│   ├── random_forest_regressor.joblib
│   ├── decision_tree_regressor.joblib
│   ├── high_waste_classifier.joblib
│   └── model_metadata.json
│
├── report/                         # Academic deliverables & benchmark data
│   ├── project_report.md           # Full 30-section academic project report
│   ├── project_report.pdf          # Compiled publication-ready PDF report
│   ├── model_comparison.json       # Exported comparative benchmark metrics (JSON)
│   ├── model_comparison.csv        # Exported comparative benchmark metrics (CSV)
│   ├── viva_preparation.md         # 20 technical viva questions and answers
│   ├── generate_pdf_report.py      # ReportLab PDF compiler script
│   └── generate_presentation.py    # PowerPoint presentation builder
│
└── screenshots/                    # Live execution screenshots
    ├── README.md
    ├── 01_dashboard_overview.png
    ├── 02_food_waste_analytics.png
    ├── 03_predict_future_leftovers.png
    ├── 04_prediction_result.png
    ├── 05_model_evaluation.png
    ├── 06_feature_importances.png
    └── evaluation_metrics_plot.png
```

---

## 3. Installation & Setup Instructions

### Step 1: Clone or Extract the Project
Extract the project folder or navigate to the workspace directory:
```bash
cd "c:/Users/suraj/OneDrive/Desktop/MongoDB CA Project"
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` and verify your MongoDB connection:
```ini
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=mess_food_waste_db
MESS_CAPACITY=1200
ESTIMATED_COST_PER_KG=45.0
```

---

## 4. Execution Workflow

### Step 1: Bootstrap and Seed MongoDB
Initializes `$jsonSchema` validation, compound indexes, and seeds 1,500 historical meal records:
```bash
python scripts/seed_database.py
```

### Step 2: Execute MongoDB Aggregation Pipelines
Executes all 6 analytical pipelines natively inside MongoDB and prints formatted tables:
```bash
python scripts/run_aggregations.py
```

### Step 3: Train Machine Learning Models
Trains both **Random Forest Regressor** and **Decision Tree Regressor**, along with the **High-Waste Classifier**, using an identical chronological split:
```bash
python ml/train_model.py
```

### Step 4: Run Comparative Evaluation
Evaluates both regression models and the baseline on the held-out test set, generating diagnostic plots:
```bash
python ml/evaluate.py
```

### Step 5: Run Automated Test Suite
Executes all 21 unit and integration tests across 5 test suites (100% pass rate):
```bash
python -m pytest tests/ -v
```

### Step 6: Launch the Interactive Streamlit Dashboard
```bash
python -m streamlit run app.py
```
Open your browser to `http://localhost:8501` to interact with the system.

---

## 5. Machine Learning Evaluation & Comparison Results

Evaluated on the exact same held-out chronological test partition (301 meals, 20% unseen data):

| Evaluation Metric | Random Forest Regressor | Decision Tree Regressor | Historical Baseline | Selected Advantage |
| :--- | :--- | :--- | :--- | :--- |
| **Mean Absolute Error (MAE)** | **14.229 kg** | 14.645 kg | 15.412 kg | **RF is 0.416 kg better; +7.68% gain over baseline** |
| **Root Mean Squared Error (RMSE)** | **19.514 kg** | 19.683 kg | 20.835 kg | **RF suppresses high-error outlier spikes** |
| **Coefficient of Determination (R²)** | **0.4959** | 0.4871 | 0.4254 | **RF explains ~50% of surplus variance** |
| **MAE Gain vs Baseline** | **+7.68%** | **+4.98%** | 0.00% (Ref) | Both algorithms substantially outperform heuristic |
| **Model Paradigm** | Ensemble Bagging (100 trees) | Single CART Tree (depth=6) | Stratified Mean | Dual-model flexibility |
| **Operational Status** | **Primary Production Model** | **Secondary Audit Model** | Reference Baseline | Full operational coverage |

### High-Waste Classifier Performance (> 35 kg Threshold):
- **Accuracy:** 83.39%
- **Precision:** 77.56%
- **Recall:** 88.97% (catches ~89% of severe overproduction meals before cooking begins)
- **F1-Score:** 82.88%

### Model Selection Rationale:
- **Random Forest Regressor** is chosen as the primary production engine because ensembling 100 bootstrap de-correlated trees smooths discrete step-function splits and reduces variance on unseen operational test days, achieving lower MAE (14.229 vs 14.645 kg) and higher R² (0.4959 vs 0.4871).
- **Decision Tree Regressor** is retained as an interpretable secondary model, offering transparent, auditable decision paths that mess supervisors can inspect.

---

## 6. Academic Deliverables & Faculty Viva
- **Complete Academic Report (PDF):** [`report/project_report.pdf`](file:///report/project_report.pdf)
- **Full Report Markdown:** [`report/project_report.md`](file:///report/project_report.md)
- **Comparative Benchmark Data:** [`report/model_comparison.json`](file:///report/model_comparison.json) & [`report/model_comparison.csv`](file:///report/model_comparison.csv)
- **Presentation Slides (PPTX - 12 Slides):** [`presentation.pptx`](file:///presentation.pptx)
- **Technical Viva Q&A Guide (20 Questions):** [`report/viva_preparation.md`](file:///report/viva_preparation.md)
- **Native MongoDB Queries:** [`queries.mongodb.js`](file:///queries.mongodb.js)
