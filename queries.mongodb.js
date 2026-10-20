/**
 * MongoDB Shell Queries & Aggregation Pipelines (mongosh / MongoDB Compass)
 * Project: Mess Food Waste Forecasting System Using MongoDB, PyMongo, and Random Forest Regression
 * Course: CSE494 Intelligent NoSQL Databases CA2 | Lovely Professional University
 * Database: mess_food_waste_db
 */

// Switch to project database
use("mess_food_waste_db");

// =====================================================================
// 1. COLLECTION SCHEMA VALIDATION SETUP
// =====================================================================

// Apply strict JSON Schema Validator to meal_records
db.runCommand({
  collMod: "meal_records",
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: [
        "meal_id",
        "meal_date",
        "meal_type",
        "day_of_week",
        "expected_attendance",
        "actual_attendance",
        "total_prepared_kg",
        "total_served_kg",
        "total_leftover_kg",
        "recorded_at"
      ],
      properties: {
        meal_id: { bsonType: "string" },
        meal_date: { bsonType: "string", pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$" },
        meal_type: { enum: ["Breakfast", "Lunch", "Snacks", "Dinner"] },
        day_of_week: { enum: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] },
        expected_attendance: { bsonType: ["int", "long"], minimum: 0 },
        actual_attendance: { bsonType: ["int", "long"], minimum: 0 },
        total_prepared_kg: { bsonType: ["double", "int", "long"], minimum: 0.0 },
        total_served_kg: { bsonType: ["double", "int", "long"], minimum: 0.0 },
        total_leftover_kg: { bsonType: ["double", "int", "long"], minimum: 0.0 },
        total_waste_kg: { bsonType: ["double", "int", "long"], minimum: 0.0 }
      }
    }
  },
  validationLevel: "strict",
  validationAction: "error"
});

// =====================================================================
// 2. DEMONSTRATION OF REJECTED INVALID DOCUMENT
// =====================================================================
// This insert will fail with DocumentValidationFailure due to negative leftover and invalid meal_type
try {
  db.meal_records.insertOne({
    meal_id: "TEST_REJECTED_001",
    meal_date: "2026-10-13",
    meal_type: "MidnightFeast", // INVALID: Not in permitted enum
    day_of_week: "Tuesday",
    expected_attendance: 500,
    actual_attendance: 480,
    total_prepared_kg: 100.0,
    total_served_kg: 120.0,
    total_leftover_kg: -20.0, // INVALID: Negative quantity
    recorded_at: new Date()
  });
} catch (e) {
  print("Document correctly rejected by MongoDB JSON Schema validation: " + e.message);
}

// =====================================================================
// 3. CRUD DEMONSTRATIONS
// =====================================================================

// CREATE
db.menus.insertOne({
  menu_id: "MENU_20261014_LUNCH",
  meal_type: "Lunch",
  menu_date: "2026-10-14",
  estimated_students: 850,
  food_items: [
    { item_name: "Steamed Rice", category: "Rice & Breads", planned_quantity_kg: 120.0 },
    { item_name: "Dal Tadka", category: "Curry & Dal", planned_quantity_kg: 85.0 }
  ],
  created_at: new Date()
});

// READ: Find all Lunch meals where leftovers exceeded 80 kg
db.meal_records.find(
  { meal_type: "Lunch", total_leftover_kg: { $gt: 80 } },
  { meal_id: 1, meal_date: 1, expected_attendance: 1, actual_attendance: 1, total_prepared_kg: 1, total_leftover_kg: 1, _id: 0 }
).sort({ total_leftover_kg: -1 }).limit(5);

// UPDATE: Correct attendance count
db.meal_records.updateOne(
  { meal_id: "MEAL_20250101_LUNCH" },
  { $set: { actual_attendance: 875 } }
);

// DELETE: Deliberately remove test record
db.meal_records.deleteOne({ meal_id: "TEST_REJECTED_001" });

// =====================================================================
// 4. AGGREGATION PIPELINES (THE 6 CORE PIPELINES)
// =====================================================================

// Pipeline 1: Average Leftovers by Meal Type
db.meal_records.aggregate([
  {
    $group: {
      _id: "$meal_type",
      meal_count: { $sum: 1 },
      avg_prepared_kg: { $avg: "$total_prepared_kg" },
      total_leftover_kg: { $sum: "$total_leftover_kg" },
      avg_leftover_kg: { $avg: "$total_leftover_kg" }
    }
  },
  {
    $project: {
      meal_type: "$_id",
      _id: 0,
      meal_count: 1,
      avg_prepared_kg: { $round: ["$avg_prepared_kg", 2] },
      total_leftover_kg: { $round: ["$total_leftover_kg", 2] },
      avg_leftover_kg: { $round: ["$avg_leftover_kg", 2] },
      leftover_percentage: {
        $round: [
          { $multiply: [{ $divide: ["$total_leftover_kg", { $cond: [{ $eq: ["$avg_prepared_kg", 0] }, 1, { $multiply: ["$avg_prepared_kg", "$meal_count"] }] }] }, 100] },
          2
        ]
      }
    }
  },
  { $sort: { avg_leftover_kg: -1 } }
]);

// Pipeline 2: Daily Food Waste Trends
db.meal_records.aggregate([
  {
    $group: {
      _id: "$meal_date",
      meals_count: { $sum: 1 },
      total_prepared_kg: { $sum: "$total_prepared_kg" },
      total_leftover_kg: { $sum: "$total_leftover_kg" },
      total_plate_waste_kg: { $sum: "$total_waste_kg" }
    }
  },
  {
    $project: {
      date: "$_id",
      _id: 0,
      total_prepared_kg: { $round: ["$total_prepared_kg", 2] },
      total_leftover_kg: { $round: ["$total_leftover_kg", 2] },
      total_plate_waste_kg: { $round: ["$total_plate_waste_kg", 2] },
      waste_percentage: {
        $round: [
          { $multiply: [{ $divide: ["$total_leftover_kg", "$total_prepared_kg"] }, 100] },
          2
        ]
      }
    }
  },
  { $sort: { date: -1 } },
  { $limit: 10 }
]);

// Pipeline 3: Food Items with Highest Leftovers ($unwind)
db.meal_records.aggregate([
  { $unwind: "$menu_items" },
  {
    $group: {
      _id: { item: "$menu_items.item_name", category: "$menu_items.category" },
      times_served: { $sum: 1 },
      total_prepared_kg: { $sum: "$menu_items.prepared_kg" },
      total_leftover_kg: { $sum: "$menu_items.leftover_kg" },
      avg_leftover_kg: { $avg: "$menu_items.leftover_kg" }
    }
  },
  {
    $project: {
      item_name: "$_id.item",
      category: "$_id.category",
      _id: 0,
      times_served: 1,
      total_prepared_kg: { $round: ["$total_prepared_kg", 2] },
      total_leftover_kg: { $round: ["$total_leftover_kg", 2] },
      avg_leftover_kg: { $round: ["$avg_leftover_kg", 2] }
    }
  },
  { $sort: { total_leftover_kg: -1 } },
  { $limit: 10 }
]);

// Pipeline 4: Attendance Bands vs Leftovers
db.meal_records.aggregate([
  {
    $project: {
      expected_attendance: 1,
      actual_attendance: 1,
      total_prepared_kg: 1,
      total_leftover_kg: 1,
      attendance_band: {
        $switch: {
          branches: [
            { case: { $lt: ["$actual_attendance", 450] }, then: "1. Low (<450)" },
            { case: { $and: [{ $gte: ["$actual_attendance", 450] }, { $lt: ["$actual_attendance", 700] }] }, then: "2. Medium (450-700)" },
            { case: { $and: [{ $gte: ["$actual_attendance", 700] }, { $lt: ["$actual_attendance", 950] }] }, then: "3. High (700-950)" }
          ],
          default: "4. Very High (950+)"
        }
      }
    }
  },
  {
    $group: {
      _id: "$attendance_band",
      meal_count: { $sum: 1 },
      avg_expected: { $avg: "$expected_attendance" },
      avg_actual: { $avg: "$actual_attendance" },
      avg_prepared_kg: { $avg: "$total_prepared_kg" },
      avg_leftover_kg: { $avg: "$total_leftover_kg" }
    }
  },
  {
    $project: {
      attendance_band: "$_id",
      _id: 0,
      meal_count: 1,
      avg_expected: { $round: ["$avg_expected", 1] },
      avg_actual: { $round: ["$avg_actual", 1] },
      avg_prepared_kg: { $round: ["$avg_prepared_kg", 2] },
      avg_leftover_kg: { $round: ["$avg_leftover_kg", 2] }
    }
  },
  { $sort: { attendance_band: 1 } }
]);

// Pipeline 5: Weekday versus Weekend Surplus Analysis
db.meal_records.aggregate([
  {
    $project: {
      day_of_week: 1,
      total_prepared_kg: 1,
      total_leftover_kg: 1,
      actual_attendance: 1,
      day_category: {
        $cond: [
          { $in: ["$day_of_week", ["Saturday", "Sunday"]] },
          "Weekend",
          "Weekday"
        ]
      }
    }
  },
  {
    $group: {
      _id: "$day_category",
      meal_count: { $sum: 1 },
      avg_attendance: { $avg: "$actual_attendance" },
      avg_prepared_kg: { $avg: "$total_prepared_kg" },
      avg_leftover_kg: { $avg: "$total_leftover_kg" }
    }
  },
  {
    $project: {
      day_category: "$_id",
      _id: 0,
      meal_count: 1,
      avg_attendance: { $round: ["$avg_attendance", 1] },
      avg_prepared_kg: { $round: ["$avg_prepared_kg", 2] },
      avg_leftover_kg: { $round: ["$avg_leftover_kg", 2] }
    }
  },
  { $sort: { day_category: 1 } }
]);

// Pipeline 6: Monthly Waste Summary & Financial Loss in INR
db.meal_records.aggregate([
  {
    $project: {
      year_month: { $substr: ["$meal_date", 0, 7] },
      total_prepared_kg: 1,
      total_leftover_kg: 1,
      total_waste_kg: { $ifNull: ["$total_waste_kg", 0.0] }
    }
  },
  {
    $group: {
      _id: "$year_month",
      meals_count: { $sum: 1 },
      total_prepared_kg: { $sum: "$total_prepared_kg" },
      total_leftover_kg: { $sum: "$total_leftover_kg" },
      total_plate_waste_kg: { $sum: "$total_waste_kg" }
    }
  },
  {
    $project: {
      month: "$_id",
      _id: 0,
      meals_count: 1,
      total_prepared_kg: { $round: ["$total_prepared_kg", 2] },
      total_leftover_kg: { $round: ["$total_leftover_kg", 2] },
      total_plate_waste_kg: { $round: ["$total_plate_waste_kg", 2] },
      estimated_loss_inr: { $round: [{ $multiply: ["$total_leftover_kg", 45.0] }, 2] }
    }
  },
  { $sort: { month: 1 } }
]);
