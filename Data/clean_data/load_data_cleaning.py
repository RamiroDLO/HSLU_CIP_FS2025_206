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
YAHOO_SPOT_DATA_PATH = PROJECT_ROOT / "API_data_pull" / "yahoo_spot.csv"


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

output_dir = PROJECT_ROOT / "Analysis" / "Final Data"
output_dir.mkdir(parents=True, exist_ok=True)

yahoo_clean_path = output_dir / "yahoo_spot_cleaned.csv"

yahoo_spot_df.to_csv(yahoo_clean_path, index=False, sep=",")


print(f"   ✓ Yahoo Spot: {yahoo_clean_path.relative_to(PROJECT_ROOT)}")
print(f"   Ready for analysis scripts.")
