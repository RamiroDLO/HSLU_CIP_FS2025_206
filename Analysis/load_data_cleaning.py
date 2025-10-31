""" script to load prepared datasets."""
# %% cell_1
# python3 -m pip install dtale missingno matplotlib
from pathlib import Path
import time
import dtale
import dtale.app as dtale_app
import pandas as pd
import matplotlib.pyplot as plt
import missingno as msno
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer


# %% paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

AUTOSCOUT_DATA_PATH = PROJECT_ROOT / "cleaned_autoscout_data_complete.csv"
YAHOO_SPOT_DATA_PATH = PROJECT_ROOT / "API_data_pull" / "yahoo_spot.csv"


# %% load_autoscout
print("🔍 Locating cleaned AutoScout dataset...")
autoscout_path = AUTOSCOUT_DATA_PATH
if not autoscout_path.exists():
    raise FileNotFoundError(f"AutoScout data not found at {autoscout_path}")

print(f" Reading {autoscout_path}...")
autoscout_df = pd.read_csv(autoscout_path, sep=";")

new_vehicle_mask = autoscout_df["production_date"] == "Neues Fahrzeug"
new_vehicle_count = int(new_vehicle_mask.sum())
if new_vehicle_count:
    autoscout_df.loc[new_vehicle_mask, "production_date"] = "102.025"

print(
    " AutoScout dataset loaded:",
    f"   Rows: {autoscout_df.shape[0]}",
    f"   Columns: {autoscout_df.shape[1]}",
    sep="\n",
)
if new_vehicle_count:
    print(f"    Replaced 'Neues Fahrzeug' in production_date for {new_vehicle_count} rows (set to 102.025).")


# %% impute_consumption
print("\n🛠️ Imputing missing consumption_l_per_100km values...")

autoscout_df["consumption_l_per_100km"] = pd.to_numeric(
    autoscout_df["consumption_l_per_100km"], errors="coerce"
)

consumption_missing_before = autoscout_df["consumption_l_per_100km"].isna().sum()

if consumption_missing_before:
    imputer = IterativeImputer(random_state=42, max_iter=10, sample_posterior=False)
    autoscout_df[["consumption_l_per_100km"]] = imputer.fit_transform(
        autoscout_df[["consumption_l_per_100km"]]
    )
    consumption_missing_after = autoscout_df["consumption_l_per_100km"].isna().sum()
    consumption_mean = autoscout_df["consumption_l_per_100km"].mean()
    print(
        "   Filled missing consumption values:",
        f"{consumption_missing_before - consumption_missing_after} rows",
        f"(mean now {consumption_mean:.2f} L/100km)",
    )
else:
    print("   No missing consumption values detected.")


# %% load_yahoo
print("\n🔍 Locating Yahoo spot dataset...")
yahoo_spot_path = YAHOO_SPOT_DATA_PATH
if not yahoo_spot_path.exists():
    raise FileNotFoundError(f"Yahoo spot data not found at {yahoo_spot_path}")

print(f" Reading {yahoo_spot_path}...")
yahoo_spot_df = pd.read_csv(yahoo_spot_path, sep=",")
print(
    " Yahoo spot dataset loaded:",
    f"   Rows: {yahoo_spot_df.shape[0]}",
    f"   Columns: {yahoo_spot_df.shape[1]}",
    sep="\n",
)


# %% clean_yahoo_commodities
print("\n🛠️ Cleaning Yahoo commodity spot data...")

# Convert Date to datetime
yahoo_spot_df["Date"] = pd.to_datetime(yahoo_spot_df["Date"], format="%Y-%m-%d", errors="coerce")

# Convert commodity columns from German decimal format (comma) to float
commodity_cols = [
    "WTI_Spot", "Copper_Spot", "Lithium_Spot",
    "Aluminium_Spot", "Steel_Spot", "Nickel_Spot", "Cobalt_Spot"
]
for col in commodity_cols:
    yahoo_spot_df[col] = (
        yahoo_spot_df[col]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )

missing_before = yahoo_spot_df[commodity_cols].isna().sum().sum()
print(f"   Missing commodity values before imputation: {missing_before}")

# Fill missing values with 7-day rolling mean
def fill_with_rolling_mean(df, columns, window=7):
    df_filled = df.copy()
    for col in columns:
        filled_series = df_filled[col].copy()
        for idx in df_filled[df_filled[col].isna()].index:
            prev_values = df_filled.loc[:idx, col].dropna().tail(window)
            if len(prev_values) > 0:
                filled_series.loc[idx] = prev_values.mean()
        df_filled[col] = filled_series
    return df_filled

yahoo_spot_df = fill_with_rolling_mean(yahoo_spot_df, commodity_cols, window=7)

missing_after = yahoo_spot_df[commodity_cols].isna().sum().sum()
print(f"   Missing commodity values after imputation: {missing_after}")

# Round to 2 decimals
yahoo_spot_df[commodity_cols] = yahoo_spot_df[commodity_cols].round(2)
print(f"   Rounded commodity values to 2 decimals.")


print("\n Datasets are ready as 'autoscout_df' and 'yahoo_spot_df'.")


# %% save_cleaned_data
print("\n💾 Saving cleaned datasets...")

output_dir = PROJECT_ROOT / "Analysis" / "cleaned_data"
output_dir.mkdir(parents=True, exist_ok=True)

autoscout_clean_path = output_dir / "autoscout_cleaned.csv"
yahoo_clean_path = output_dir / "yahoo_spot_cleaned.csv"

autoscout_df.to_csv(autoscout_clean_path, index=False, sep=";")
yahoo_spot_df.to_csv(yahoo_clean_path, index=False, sep=",")

print(f"   ✓ AutoScout: {autoscout_clean_path.relative_to(PROJECT_ROOT)}")
print(f"   ✓ Yahoo Spot: {yahoo_clean_path.relative_to(PROJECT_ROOT)}")
print(f"   Ready for analysis scripts.")


# %% dtale_views
print("\n Launching D-Tale dataframe views (ensure 'dtale' is installed)...")
# Clear any cached D-Tale instances to avoid stale configuration
dtale.global_state.cleanup()

dtale_app.ACTIVE_HOST = "localhost"
autoscout_view = dtale.show(
    autoscout_df,
    name="autoscout data",
    locked=[],
    open_browser=True,
    port=4000,
    host="localhost"
)
if autoscout_view:
    print(f"   AutoScout D-Tale: {autoscout_view.main_url()}")

time.sleep(1)

yahoo_spot_view = dtale.show(
    yahoo_spot_df,
    name="yahoo spot cleaned",
    locked=[],
    open_browser=True,
    port=4001,
    host="localhost"
)
if yahoo_spot_view:
    print(f"   Yahoo Spot (Cleaned) D-Tale: {yahoo_spot_view.main_url()}")

print("\n   D-Tale servers running on localhost:4000 and localhost:4001")
print("   Press Ctrl+C to stop.")
try:
    input()
except KeyboardInterrupt:
    print("\n   Shutting down D-Tale servers...")
finally:
    dtale.global_state.cleanup()

