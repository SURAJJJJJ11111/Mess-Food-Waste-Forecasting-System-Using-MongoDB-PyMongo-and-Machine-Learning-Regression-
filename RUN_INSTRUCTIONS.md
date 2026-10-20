# Mess Food Waste Forecasting System: Execution Guide & Command Reference

---

## ⚡ ULTRA FAST ONE-CLICK EXECUTION (Using Python Scripts)

We have created two all-in-one automation scripts for you:

### 1️⃣ Run this ONLY ONCE (First Time Setup):
```powershell
python first_time_setup.py
```
> *This automatically checks MongoDB, creates collections and validation schemas, seeds 1,500 historical meal records, trains the Random Forest and Decision Tree models, and generates all evaluation plots!*

### 2️⃣ Run this EVERY TIME (Whenever You Want to Launch the Project):
```powershell
python run_project.py
```
> *This checks your saved models and launches the interactive Streamlit dashboard at `http://localhost:8501`.*

---

## 🟢 MANUAL COMMANDS: EVERY TIME YOU RUN OR DEMO
> **If you prefer manual commands without `run_project.py`:**

Open PowerShell or Command Prompt in the project folder and run:

```powershell
# Step 1: Open project folder
cd "c:\Users\suraj\OneDrive\Desktop\MongoDB CA Project"

# Step 2: Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Step 3: Run the web application!
streamlit run app.py
```
> The dashboard will open automatically in your browser at `http://localhost:8501`.

---

## 🟡 MANUAL COMMANDS: RUN ONLY ONCE (Step-by-Step)
> **If you prefer running individual setup steps manually instead of `first_time_setup.py`:**

```powershell
# 1. Navigate to project root
cd "c:\Users\suraj\OneDrive\Desktop\MongoDB CA Project"

# 2. Create Python virtual environment
python -m venv .venv

# 3. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Install all required dependencies
pip install -r requirements.txt

# 5. Initialize MongoDB database, collections, schemas & indexes
python database/setup.py

# 6. Seed MongoDB with the 1,500 historical meal records
python scripts/seed_database.py

# 7. Train & save Machine Learning models to models/ folder
python ml/train_model.py

# 8. Generate evaluation charts & diagnostic plots to report/ folder
python ml/evaluate.py
```

---

## 📋 Quick Comparison Table: What Runs When?

| Command | Category | How Often to Run? | What Does It Do? |
| :--- | :--- | :--- | :--- |
| **`streamlit run app.py`** | **Daily / Demo** | **EVERY TIME** | **Opens the interactive web application in your browser.** |
| `.\.venv\Scripts\Activate.ps1` | **Environment** | When opening a new terminal | Activates the project's Python virtual environment. |
| `pip install -r requirements.txt` | **Setup** | **Only ONCE** | Installs PyMongo, Scikit-Learn, Streamlit, etc. |
| `python database/setup.py` | **Setup** | **Only ONCE** | Creates MongoDB collections & schema validators. |
| `python scripts/seed_database.py`| **Setup** | **Only ONCE** | Permanently inserts 1,500 records into MongoDB. |
| `python ml/train_model.py` | **Setup** | **Only ONCE** | Trains Random Forest & Decision Tree and saves `.joblib` files. |
| `python ml/evaluate.py` | **Setup** | **Only ONCE** | Creates evaluation metrics plot images on disk. |
| `python scripts/run_aggregations.py`| **Testing** | Optional / Whenever needed | Tests the 6 aggregation pipelines in the terminal. |
| `python -m pytest tests/ -v` | **Testing** | Optional / For grading | Runs all 21 automated tests. |
| `python report/generate_pdf_report.py` | **Deliverable** | Optional / As needed | Generates the academic PDF project report. |
| `python report/generate_presentation.py`| **Deliverable** | Optional / As needed | Generates the 12-slide PowerPoint presentation (`presentation.pptx`). |

---

## Detailed Step-by-Step Instructions

### Step 0: System Prerequisites

Before running the project, verify that the following are installed:
1. **Python 3.10+ (Recommended: Python 3.12)**
   - Check with:
     ```bash
     python --version
     ```
2. **MongoDB Community Server (8.x or 7.x) OR MongoDB Atlas Connection**
   - Check if MongoDB service is running locally on port 27017:
     ```powershell
     Get-Service MongoDB
     ```
   - If not running, start it:
     ```powershell
     Start-Service MongoDB
     # Or manually via mongod:
     mongod --dbpath "C:\data\db"
     ```

---

### Step 1: Open Terminal & Set Up Virtual Environment

Open PowerShell or Command Prompt, navigate to the project directory, and create an isolated virtual environment:

```powershell
cd "c:\Users\suraj\OneDrive\Desktop\MongoDB CA Project"

# Create virtual environment named .venv
python -m venv .venv

# Activate on Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# (If PowerShell throws an execution policy error, run once:
#  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser)

# Or activate on Command Prompt (cmd.exe):
.\.venv\Scripts\activate.bat

# Or activate on Linux / macOS / Git Bash:
source .venv/bin/activate
```

---

### Step 2: Install Project Dependencies

Install all required libraries including PyMongo, scikit-learn, Streamlit, Plotly, Pandas, ReportLab, and pytest:

```bash
pip install -r requirements.txt
```

Verify key packages:
```bash
python -c "import pymongo, sklearn, streamlit, plotly, reportlab; print('All core libraries installed successfully!')"
```

---

### Step 3: Configure Environment Variables

The project reads settings from `.env`. A default `.env` file is already included, or you can copy `.env.example`:

```powershell
# Verify or create .env from .env.example
copy .env.example .env
```

Default content of `.env`:
```ini
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=mess_food_waste_db
MESS_CAPACITY=1200
ESTIMATED_COST_PER_KG=45.0
```

*(Note: If connecting to MongoDB Atlas, replace `MONGODB_URI` with your connection string: `mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority`)*.

---

### Step 4: Initialize MongoDB Collections & Validators

Builds the database collections (`meal_records`, `predictions`), registers strict `$jsonSchema` validators, and creates single-field, compound, and multikey indexes:

```bash
python database/setup.py
```

**Expected Output:**
```
======================================================================
INITIALIZING MONGODB SETUP: mess_food_waste_db
======================================================================
Connected to MongoDB successfully.
Collection 'meal_records' created with $jsonSchema validation.
Collection 'predictions' created with $jsonSchema validation.
Indexes created successfully for 'meal_records'.
Indexes created successfully for 'predictions'.
Database setup complete!
======================================================================
```

---

### Step 5: Seed MongoDB with Historical Records

Populates the MongoDB database with 1,500 historical meal records across ~375 calendar days:

```bash
python scripts/seed_database.py
```

**Expected Output:**
```
Connecting to MongoDB: mongodb://localhost:27017/ ...
Loaded 1500 records from data/historical_meal_records.json
Inserted 1500 records into 'meal_records' collection.
Verification: Total documents in 'meal_records' = 1500
Seeding completed successfully!
```

---

### Step 6: Test Native Aggregation Pipelines

Executes the 6 server-side MongoDB analytical aggregation pipelines via Python CLI:

```bash
python scripts/run_aggregations.py
```

**What this outputs:**
1. Average leftovers by meal type (Breakfast, Lunch, Snacks, Dinner).
2. Daily waste trend summary.
3. Top 10 most wasted items (via `$unwind: "$menu_items"`).
4. Waste grouped by attendance volume bands (via `$switch`).
5. Weekend vs. Weekday operational waste comparison.
6. Total financial loss and $CO_2$ equivalent impact summary.

---

### Step 7: Train and Benchmark Machine Learning Models

Trains both **Random Forest Regressor** and **Decision Tree Regressor**, benchmarks against the **Historical Mean Baseline**, trains the **High-Waste Classifier**, and exports model artifacts and comparison metrics:

```bash
python ml/train_model.py
```

**Saved Artifacts:**
- `models/random_forest_regressor.joblib`
- `models/decision_tree_regressor.joblib`
- `models/high_waste_classifier.joblib`
- `models/model_metadata.json`
- `report/model_comparison.json`
- `report/model_comparison.csv`

**Expected Output:**
```
=================================================================
ALGORITHM COMPARISON RESULTS (ON UNSEEN TEST SET)
=================================================================
Model                      | MAE (kg)  | RMSE (kg) | R²      | vs Base  
-----------------------------------------------------------------
Decision Tree Regressor    | 14.645    | 19.683    | 0.4871  |  +4.98%
Random Forest Regressor    | 14.229    | 19.514    | 0.4959  |  +7.68%
Historical Mean Baseline   | 15.412    | 20.835    | 0.4254  |   0.00%
=================================================================
High-Waste Classifier (>35kg): Accuracy=83.39%, Recall=88.97%, F1=82.88%
```

---

### Step 8: Generate Diagnostic Plots & Charts

Evaluates model predictions and generates a 4-panel diagnostic plot (Actual vs. Predicted scatter plot, residual errors, cumulative distribution, and error histograms):

```bash
python ml/evaluate.py
```

**Saved Output:**
- `report/evaluation_metrics_plot.png`
- `screenshots/07_evaluation_metrics_plot.png`
- `screenshots/evaluation_metrics_plot.png`

---

### Step 9: Run Automated Test Suite

Runs the automated test suite (21 unit and integration tests) using pytest:

```bash
# Run all tests with verbose output:
python -m pytest tests/ -v

# Run specific test modules:
python -m pytest tests/test_model_comparison.py -v
python -m pytest tests/test_validation.py -v
python -m pytest tests/test_crud.py -v
python -m pytest tests/test_aggregations.py -v
python -m pytest tests/test_prediction.py -v
```

---

### Step 10: Launch Interactive Streamlit Web Application

Starts the multi-page web application in your default browser:

```bash
streamlit run app.py
```

- **Local URL:** `http://localhost:8501`
- **Network URL:** `http://<your-local-ip>:8501`

**Features Available in the Web App:**
1. **Overview Dashboard:** Live KPI tiles, MongoDB collection count, and meal distribution charts.
2. **Food Waste Analytics:** Interactive Plotly charts driven by the 6 MongoDB Aggregation Pipelines.
3. **Predict Future Leftovers:** Live kitchen simulator. Switch between **Random Forest** and **Decision Tree**, input diner counts and weather, and get immediate forecasts + buffer recommendations.
4. **Model Comparison & Viva Prep:** Side-by-side performance comparison and interactive viva question browser.
5. **Operational CRUD Operations:** Add new meal records, update attendances, and delete documents with real-time schema validation.

---

### Step 11: Compile Academic PDF Report & PowerPoint Presentation

Regenerate the publication-grade PDF report and PowerPoint presentation:

```bash
# 1. Generate academic PDF project report (ReportLab)
python report/generate_pdf_report.py

# Output: report/project_report.pdf

# 2. Generate 12-slide PowerPoint presentation (python-pptx)
python report/generate_presentation.py

# Output: presentation.pptx
```

---

### Step 12: Run Native MongoDB Shell (`mongosh`) Queries

If you have `mongosh` installed, you can execute the raw JavaScript queries and aggregations:

```bash
# Connect to local database and execute queries.mongodb.js
mongosh "mongodb://localhost:27017/mess_food_waste_db" queries.mongodb.js
```

Or open MongoDB Compass, connect to `mongodb://localhost:27017/`, and paste queries from [queries.mongodb.js](file:///c:/Users/suraj/OneDrive/Desktop/MongoDB%20CA%20Project/queries.mongodb.js) into the Aggregations tab.

---

## Troubleshooting & Frequently Asked Questions

### 1. `pymongo.errors.ServerSelectionTimeoutError: localhost:27017: No connection could be made...`
- **Cause:** The MongoDB service is stopped or not installed.
- **Solution:**
  - In Windows PowerShell (Administrator):
    ```powershell
    Start-Service MongoDB
    ```
  - Or manually start `mongod`:
    ```powershell
    mongod --dbpath "C:\Program Files\MongoDB\Server\8.0\data"
    ```
  - If using MongoDB Atlas, verify your `.env` contains the valid Atlas URI and your IP address is whitelisted in Atlas Network Access.

### 2. `ModuleNotFoundError: No module named '...'`
- **Cause:** Virtual environment is either not activated or dependencies are missing.
- **Solution:**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

### 3. Streamlit Port 8501 already in use
- **Cause:** Another instance of Streamlit is running.
- **Solution:**
  ```bash
  streamlit run app.py --server.port 8502
  ```

### 4. PowerShell `Script Execution Policy` Error
- **Cause:** PowerShell blocks running unsigned scripts by default.
- **Solution:**
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

### 5. `FileNotFoundError: models/random_forest_regressor.joblib`
- **Cause:** Model files have not been generated yet.
- **Solution:**
  ```bash
  python ml/train_model.py
  ```
