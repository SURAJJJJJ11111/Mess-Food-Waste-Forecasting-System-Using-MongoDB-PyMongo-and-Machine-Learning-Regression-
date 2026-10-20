# TECHNICAL VIVA PREPARATION GUIDE
## CSE494: Intelligent NoSQL Databases — CA2 Project Viva
### Topic: Mess Food Waste Forecasting System Using MongoDB, PyMongo, and Random Forest Regression
**Institution:** Lovely Professional University

---

### Question 1: Why did you choose MongoDB instead of a Relational Database (RDBMS like MySQL or PostgreSQL)?
**Answer:**
1. **Dynamic Itemized Menus:** In a university dining hall, each meal session features an arbitrary number of dishes with variable categories and portion sizes. In an RDBMS, this requires normalized multi-table schemas with foreign key JOINs across `meals`, `meal_items`, and `dishes`. In MongoDB, the `menu_items` array is naturally embedded within the parent `meal_records` document.
2. **Atomic Single-Document Writes:** A meal session's preparation and leftover quantities can be written in a single atomic operation without multi-table transaction overhead.
3. **Native Aggregation Pipelines:** MongoDB provides expressive aggregation stages (`$group`, `$unwind`, `$project`, `$switch`) directly inside the database engine, avoiding the overhead of pulling raw records into Python memory for analytical reporting.

---

### Question 2: Why did you embed `menu_items` inside `meal_records` instead of creating a separate collection with references?
**Answer:**
We applied MongoDB's **1:Few Document Modeling Principle**:
- A typical meal contains only 3 to 6 distinct menu items (e.g., Rice, Dal, Paneer, Chapati, Salad).
- The items are always queried and displayed together with the parent meal session.
- Storing them embedded eliminates the need for expensive `$lookup` (JOIN) stages in real-time operational feeds and guarantees ACID atomicity at the document level.

---

### Question 3: What is BSON, and how does PyMongo interact with it?
**Answer:**
BSON stands for **Binary JSON**. It is MongoDB's internal binary-encoded serialization format. Unlike standard JSON which only supports strings, numbers, booleans, arrays, and objects, BSON extends this with rich native data types including:
- UTC `datetime` (BSON Date)
- 64-bit Integer (`long`) and Double (`double`)
- `ObjectId`
- Binary data and Regex.
PyMongo transparently converts Python `datetime.datetime` objects into BSON Dates and handles numeric type mapping.

---

### Question 4: What is MongoDB JSON Schema Validation and how is it configured?
**Answer:**
MongoDB JSON Schema validation (`$jsonSchema`) allows database administrators to enforce schema constraints at the database engine level upon document insertion and update.
It was configured using `create_collection(validator=...)` and `collMod` in `database/setup.py`. It enforces:
- **Required fields:** `meal_id`, `meal_date`, `meal_type`, `total_prepared_kg`, `total_leftover_kg`, etc.
- **Allowed enums:** `meal_type` $\in$ `["Breakfast", "Lunch", "Snacks", "Dinner"]`.
- **Numeric bounds:** Non-negative constraints (`minimum: 0.0` for leftovers and preparation).
- **Date regex:** `^[0-9]{4}-[0-9]{2}-[0-9]{2}$`.

---

### Question 5: What is an Aggregation Pipeline in MongoDB?
**Answer:**
An Aggregation Pipeline is a framework for multi-stage data processing modeled on dataflow pipelines. Documents from a collection pass through sequential stages where each stage transforms the documents and passes the resulting stream to the next stage. Key stages implemented in this project include:
- `$match`: Filters documents based on query criteria.
- `$unwind`: Deconstructs an array field from input documents to output a document for each element.
- `$group`: Groups documents by a specified identifier key and computes accumulator metrics (`$sum`, `$avg`).
- `$project`: Reshapes documents, computes new fields, and rounds numerical outputs.
- `$sort`: Orders documents in ascending or descending sequence.

---

### Question 6: Explain how `$unwind` works in Aggregation Pipeline 3 (Top Wasted Food Items).
**Answer:**
Each document in `meal_records` contains an embedded array `menu_items` containing 3–5 items. 
`{"$unwind": "$menu_items"}` deconstructs this array so that a single meal document with 5 items becomes 5 distinct stream documents, each containing one item. 
This allows the subsequent `{"$group": {"_id": "$menu_items.item_name"}}` stage to calculate cumulative prepared and leftover kilograms for individual dishes like "Steamed Basmati Rice" or "Paneer Butter Masala" across all 1,500 historical meals.

---

### Question 7: Why choose Random Forest Regression instead of Simple Linear Regression?
**Answer:**
Food waste generation in a college mess is governed by complex, **non-linear interactions**:
- A rainy Friday during exam week produces very different dining behavior than a sunny Friday during a cultural fest.
- Linear regression assumes linear additivity and constant variance, which fails to capture these threshold effects.
- Random Forest is an ensemble of 100 decorrelated decision trees that naturally captures high-order feature interactions, handles mixed continuous and categorical variables without requiring scaling assumptions, and resists overfitting via bootstrap aggregating (bagging).

---

### Question 8: What are MAE, RMSE, and R² score, and what were your actual measured values?
**Answer:**
- **MAE (Mean Absolute Error):** Average magnitude of absolute prediction errors in kilograms:
  $$\text{MAE} = \frac{1}{n} \sum |y_i - \hat{y}_i| = \mathbf{14.167 \text{ kg}}$$
  *Meaning:* On average, predictions differ from actual unserved food by ~14.2 kg.
- **RMSE (Root Mean Squared Error):** Penalizes larger outlier errors more heavily due to squaring:
  $$\text{RMSE} = \sqrt{\frac{1}{n} \sum (y_i - \hat{y}_i)^2} = \mathbf{19.455 \text{ kg}}$$
- **R² Score (Coefficient of Determination):** Proportion of leftover variance explained by model features:
  $$R^2 = \mathbf{0.4942}$$

---

### Question 9: How did you ensure zero data leakage during machine learning model training?
**Answer:**
1. **Feature Separation:** Post-meal operational outcomes (`actual_attendance`, `total_served_kg`, `total_waste_kg`) were strictly excluded from model input features. Only pre-meal features known before cooking (`expected_attendance`, `total_prepared_kg`, `meal_type`, `day_of_week`, `weather_condition`, `prev_leftover_kg`) were used.
2. **Chronological Time-Aware Split:** Rather than random K-Fold shuffling (which would allow future records to leak into past training), the dataset was partitioned chronologically: the first 80% of dates (Jan 1, 2025 to Oct 27, 2025) formed the training set, while the subsequent 20% (Oct 28, 2025 to Jan 10, 2026) formed the unseen test set.
3. **Transformer Fitting:** Preprocessing transformers (`OneHotEncoder`, `StandardScaler`) were fit exclusively on training data.

---

### Question 10: Why is comparing against a baseline necessary, and how did your model perform?
**Answer:**
A raw error metric like "MAE of 14 kg" is meaningless without context. We benchmarked the Random Forest model against a **Historical Mean Baseline** (which predicts the historical average leftover for that meal slot from the training set).
- Baseline MAE: 15.350 kg
- Random Forest MAE: 14.167 kg
- **Improvement:** 7.71% error reduction over baseline, and a 16.78% increase in $R^2$ (from 0.4232 to 0.4942).

---

### Question 11: How does the system prevent physically impossible negative leftover predictions?
**Answer:**
Unconstrained regression models can occasionally output negative predictions for low-volume meals. In `ml/predict.py`, the inference function applies a mathematical clipping constraint:
`predicted_leftover_kg = max(0.0, round(raw_pred, 2))`
This guarantees that predicted surplus is strictly $\ge 0.0$ kg.

---

### Question 12: What indexes were created in MongoDB and why?
**Answer:**
1. `idx_unique_meal_id`: Unique index ensuring no duplicate meal IDs.
2. `idx_unique_meal_date_type`: Compound unique index on `(meal_date, meal_type)` ensuring only one record exists per meal session.
3. `idx_meal_date_desc`: Descending index on `meal_date` to accelerate chronological range queries.
4. `idx_meal_type_dow`: Compound index on `(meal_type, day_of_week)` to optimize meal-type queries.
5. `idx_meal_leftover_desc`: Descending index on `total_leftover_kg` for threshold audit queries.

---

### Question 13: What is the distinction between "leftovers" and "food waste" in this system?
**Answer:**
- **Leftovers (`total_leftover_kg`):** Edible, unserved surplus food remaining in kitchen warming trays after service. This food has never been served onto student plates, is hygienic, and can be safely repurposed or donated. This is our **primary forecasting target**.
- **Plate Waste (`total_waste_kg`):** Served food left uneaten on student plates and scraped into garbage bins. This food is contaminated and must be composted or discarded.

---

### Question 14: How does safe deletion and referential consistency work in your implementation?
**Answer:**
In `database/crud.py`, the function `delete_meal_record(db, meal_id)` deletes the meal document from `meal_records` and immediately executes a cascading deletion on `attendance_records` matching the same `meal_id`:
`db["attendance_records"].delete_many({"meal_id": meal_id})`
This ensures no orphaned attendance documents persist in the database.

---

### Question 15: What is the role of `$switch` in Aggregation Pipeline 4?
**Answer:**
`$switch` performs conditional branching similar to a SQL `CASE WHEN` statement. In Pipeline 4, it evaluates `actual_attendance` to categorize meals into 4 bands dynamically inside MongoDB:
- `< 450`: Low Attendance
- `450 - 700`: Medium Attendance
- `700 - 950`: High Attendance
- `> 950`: Very High Attendance
Subsequent pipeline stages then group by these bands to analyze how attendance estimation errors vary by hall capacity.

---

### Question 16: Why did you use `collMod` in database setup?
**Answer:**
`collMod` (Collection Modification) allows updating the `$jsonSchema` validator of an existing collection without dropping the collection or losing existing data. This makes database initialization completely **idempotent**: if collections already exist, `collMod` updates their schema; if they do not exist, `create_collection` creates them.

---

### Question 17: How is the predicted waste percentage calculated?
**Answer:**
$$\text{Predicted Waste Percentage} = \left(\frac{\text{Predicted Leftover (kg)}}{\text{Total Planned Preparation (kg)}}\right) \times 100$$
Using total planned preparation as the denominator explicitly bounds the metric between 0% and 100% and expresses what fraction of the chef's batch is expected to go unconsumed.

---

### Question 18: What actionable advice does the system provide to mess supervisors?
**Answer:**
When a supervisor inputs planned meal details:
1. It forecasts the unserved surplus in kg and percentage.
2. It translates kilograms into equivalent unserved diner meals (e.g., 58.6 kg $\approx$ 146 meals).
3. If surplus $> 35$ kg, it triggers a **High Waste Alert** and computes an adjusted recommended preparation volume (e.g., scale preparation down from 450 kg to 406 kg).

---

### Question 19: What are the limitations of synthetic simulation data?
**Answer:**
While our synthetic generator models mass conservation, attendance noise, weather, and day-of-week factors with seed 42, synthetic data cannot replicate rare real-world anomalies such as unexpected kitchen equipment breakdowns, flash food strikes, or unannounced class cancellations. Production deployment would require fine-tuning on 3–6 months of physical scale weights.

---

### Question 20: How would you scale this system for multiple campus hostel messes?
**Answer:**
1. **Multi-Tenancy:** Add a `mess_id` or `hostel_block_id` attribute to all collections and incorporate it into compound indexes `(mess_id, meal_date, meal_type)`.
2. **IoT Integration:** Connect smart digital scales via MQTT to push batch weights directly to a FastAPI / PyMongo ingestion microservice.
3. **Automated Redistribution:** Integrate automated webhook dispatch to local food bank networks when predicted leftover surplus exceeds 40 kg.
