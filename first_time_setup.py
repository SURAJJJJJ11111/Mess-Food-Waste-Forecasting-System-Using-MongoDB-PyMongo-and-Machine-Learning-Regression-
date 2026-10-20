"""
First-Time Project Setup Runner
===============================
Run this file ONCE to initialize the entire Mess Food Waste Forecasting System:
1. Verifies MongoDB connection
2. Initializes database collections, schemas, and indexes (database/setup.py)
3. Seeds 1,500 historical meal records into MongoDB (scripts/seed_database.py)
4. Trains and exports Machine Learning models (Random Forest, Decision Tree, Classifier) (ml/train_model.py)
5. Generates diagnostic evaluation plots and comparison reports (ml/evaluate.py)

Usage:
    python first_time_setup.py
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

def print_step(step_num: int, title: str):
    print("\n" + "=" * 65)
    print(f" STEP {step_num}: {title.upper()}")
    print("=" * 65)

def run_command(cmd_args, desc: str):
    print(f"-> Running: {desc}...")
    result = subprocess.run(cmd_args, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        print(f"\n[ERROR] Failed during: {desc} (Exit code: {result.returncode})")
        print("Please check the error output above.")
        sys.exit(result.returncode)
    print(f"[OK] Completed: {desc}")

def check_mongodb():
    print("-> Checking MongoDB connectivity...")
    try:
        from pymongo import MongoClient
        import config
        client = MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        print(f"[OK] Connected to MongoDB at {config.MONGODB_URI}")
    except Exception as e:
        print("\n" + "!" * 65)
        print("[ERROR] Could not connect to MongoDB server!")
        print("Please ensure MongoDB service is running on your machine.")
        print("To start MongoDB on Windows, open PowerShell as Admin and run:")
        print("    Start-Service MongoDB")
        print("Or run manually:")
        print("    mongod")
        print("!" * 65)
        sys.exit(1)

def main():
    print("\n" + "#" * 65)
    print("   MESS FOOD WASTE FORECASTING SYSTEM - ONE-CLICK SETUP")
    print("   (Run this script ONLY ONCE to initialize the project)")
    print("#" * 65)

    # Step 1: Check MongoDB Connectivity
    print_step(1, "Verify MongoDB Connection")
    check_mongodb()

    # Step 2: Initialize Database Schemas & Validators
    print_step(2, "Initialize MongoDB Collections, Schemas & Indexes")
    run_command([sys.executable, "database/setup.py"], "Database setup and validation configuration")

    # Step 3: Seed Database with Historical Records
    print_step(3, "Seed MongoDB with 1,500 Historical Meal Records")
    run_command([sys.executable, "scripts/seed_database.py"], "Seeding database with records")

    # Step 4: Train Machine Learning Models
    print_step(4, "Train & Benchmark ML Models (Random Forest vs Decision Tree)")
    run_command([sys.executable, "ml/train_model.py"], "Model training and serialization")

    # Step 5: Generate Diagnostic Evaluation Plots
    print_step(5, "Generate Diagnostic Evaluation Plots")
    run_command([sys.executable, "ml/evaluate.py"], "Evaluation plots generation")

    print("\n" + "=" * 65)
    print("   SETUP COMPLETED SUCCESSFULLY! ALL DATA & MODELS ARE READY.")
    print("=" * 65)
    print("\nFrom now on, whenever you want to run the project, simply run:")
    print("    python run_project.py\n")

if __name__ == "__main__":
    main()
