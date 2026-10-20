"""
Daily / Demo Project Runner
===========================
Run this file EVERY TIME you want to launch and use the Mess Food Waste
Forecasting System dashboard.

Usage:
    python run_project.py
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

def main():
    print("\n" + "=" * 65)
    print("   LAUNCHING MESS FOOD WASTE FORECASTING SYSTEM")
    print("   Course: CSE494 Intelligent NoSQL Databases (LPU)")
    print("=" * 65)

    # Sanity check: verify models exist
    rf_model = PROJECT_ROOT / "models" / "random_forest_regressor.joblib"
    if not rf_model.exists():
        print("\n[WARNING] Trained models not detected in models/ directory!")
        print("It looks like you haven't run the initial setup yet.")
        print("Please run the first-time setup first:")
        print("    python first_time_setup.py\n")
        sys.exit(1)

    app_path = PROJECT_ROOT / "app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]

    print("-> Starting Streamlit server...")
    print("-> Opening dashboard in your default browser at http://localhost:8501")
    print("-> Press Ctrl + C in this terminal anytime to stop the server.\n")

    try:
        subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    except KeyboardInterrupt:
        print("\n\n[OK] Streamlit application stopped cleanly. Goodbye!")

if __name__ == "__main__":
    main()
