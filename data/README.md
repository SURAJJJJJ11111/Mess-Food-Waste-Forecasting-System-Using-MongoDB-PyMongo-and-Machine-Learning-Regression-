# Mess Food Waste Dataset Documentation

## 1. Provenance and Academic Disclosure
- **Dataset Title**: Mess Historical Meal & Food Waste Operational Records
- **Nature of Data**: **Documented Synthetic Simulation** (Seed = 42)
- **Institution**: CSE494 Intelligent NoSQL Databases CA2, Lovely Professional University
- **Disclaimer**: *In compliance with academic integrity guidelines, these records are explicitly disclosed as simulated data generated via a reproducible stochastic process based on realistic college mess catering dynamics, mass conservation principles, and empirical waste benchmarks. They do not represent proprietary or real-world measurements from Lovely Professional University.*

## 2. Dataset Overview
- **Total Records**: 1,500 historical meal operational sessions
- **Temporal Coverage**: 375 consecutive days (January 1, 2025 to January 10, 2026)
- **Meals Per Day**: 4 (Breakfast, Lunch, Snacks, Dinner)
- **Storage Formats**: `historical_meal_records.csv` and `historical_meal_records.json`

## 3. Data Dictionary

| Column Name | Data Type | Units / Range | Description |
| :--- | :--- | :--- | :--- |
| `meal_id` | String | Unique ID | Primary business identifier (e.g. `MEAL_20250101_BREAKFAST`) |
| `meal_date` | String | YYYY-MM-DD | Calendar date of meal service |
| `meal_type` | String | Categorical | Meal slot: Breakfast, Lunch, Snacks, Dinner |
| `day_of_week` | String | Categorical | Monday through Sunday |
| `expected_attendance` | Integer | 250 - 1150 | Headcount forecast available prior to cooking |
| `actual_attendance` | Integer | 180 - 1200 | Actual diner headcount verified via biometric/turnstiles |
| `total_prepared_kg` | Float | 50.0 - 550.0 kg | Total edible food prepared in the kitchen |
| `total_served_kg` | Float | 40.0 - 520.0 kg | Edible quantity served onto student plates |
| `total_leftover_kg` | Float | 0.0 - 120.0 kg | **Prediction Target**: Unserved edible food remaining in containers |
| `total_waste_kg` | Float | 1.0 - 35.0 kg | Plate waste / food discarded post-consumption |
| `weather_condition` | String | Categorical | Sunny, Rainy, Pleasant, Cold |
| `special_event` | Boolean | True / False | Flag for college fests, sports meets, or exam periods |
| `prev_leftover_kg` | Float | kg | Leftovers recorded in the immediately preceding meal session |
| `prev_attendance` | Integer | Count | Attendance recorded in the immediately preceding meal session |
| `data_source` | String | Constant | `SYNTHETIC_SIMULATION` |

## 4. Physical Consistency and Conservation of Mass
The dataset strictly satisfies physical conservation rules:
$$\text{Total Prepared (kg)} = \text{Total Served (kg)} + \text{Total Leftover (kg)}$$
- $\text{Total Leftover} \ge 0.0$ kg (no physically impossible negative surplus)
- Item-level quantities reconcile with meal-level aggregates.
