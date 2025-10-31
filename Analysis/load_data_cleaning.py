"""Step-by-step script to load prepared datasets."""
# python3 -m pip install dtale
from pathlib import Path
import time
import dtale
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

AUTOSCOUT_DATA_PATH = PROJECT_ROOT / "cleaned_autoscout_data_complete.csv"
YAHOO_SPOT_DATA_PATH = PROJECT_ROOT / "API_data_pull" / "yahoo_spot.csv"


print("🔍 Locating cleaned AutoScout dataset...")
autoscout_path = AUTOSCOUT_DATA_PATH
if not autoscout_path.exists():
    raise FileNotFoundError(f"AutoScout data not found at {autoscout_path}")

print(f" Reading {autoscout_path}...")
autoscout_df = pd.read_csv(autoscout_path, sep=";")
print(
    " AutoScout dataset loaded:",
    f"   Rows: {autoscout_df.shape[0]}",
    f"   Columns: {autoscout_df.shape[1]}",
    sep="\n",
)


print("\n🔍 Locating Yahoo spot dataset...")
yahoo_spot_path = YAHOO_SPOT_DATA_PATH
if not yahoo_spot_path.exists():
    raise FileNotFoundError(f"Yahoo spot data not found at {yahoo_spot_path}")

print(f" Reading {yahoo_spot_path}...")
yahoo_spot_df = pd.read_csv(yahoo_spot_path, sep=";")
print(
    " Yahoo spot dataset loaded:",
    f"   Rows: {yahoo_spot_df.shape[0]}",
    f"   Columns: {yahoo_spot_df.shape[1]}",
    sep="\n",
)


print("\n Datasets are ready as 'autoscout_df' and 'yahoo_spot_df'.")


print("\n Launching D-Tale dataframe views (ensure 'dtale' is installed)...")
# Clear any cached D-Tale instances to avoid stale configuration
dtale.global_state.cleanup()

# Launch first view and let it fully initialize
print("   Starting AutoScout view...")
try:
    autoscout_view = dtale.show(
        autoscout_df, 
        name="autoscout data", 
        locked=[], 
        open_browser=True
    )
    if autoscout_view:
        print(f"   ✓ AutoScout: {autoscout_view.main_url()}")
except Exception as e:
    print(f"   ✗ AutoScout failed: {e}")
    autoscout_view = None

# Give first server time to bind to its port
time.sleep(1)

# Launch second view on next available port
print("   Starting Yahoo spot view...")
try:
    yahoo_spot_view = dtale.show(
        yahoo_spot_df, 
        name="yahoo spot data", 
        locked=[], 
        open_browser=True
    )
    if yahoo_spot_view:
        print(f"   ✓ Yahoo Spot: {yahoo_spot_view.main_url()}")
except Exception as e:
    print(f"   ✗ Yahoo Spot failed: {e}")
    yahoo_spot_view = None

if autoscout_view is not None or yahoo_spot_view is not None:
    print("\n   D-Tale views opened in your browser.")
    try:
        input("\nPress Enter to stop D-Tale servers...")
    except KeyboardInterrupt:
        print("\n   Shutting down...")
    finally:
        dtale.global_state.cleanup()
else:
    print("\n    No D-Tale views started successfully.")
