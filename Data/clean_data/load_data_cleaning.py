""" script to load prepared datasets."""
# %% cell_1
# python3 -m pip install pandas
from pathlib import Path
import time
import os
import pandas as pd

import os

# %% paths
yahoo_spot_df = pd.read_csv("../../Data/API_data_pull/yahoo_spot.csv", sep=",")

# %% load_yahoo
yahoo_spot_df["Date"] = pd.to_datetime(yahoo_spot_df["Date"], errors="coerce")

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
print(f"Missing commodity values before imputation: {missing_before}")

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
print(f"Missing commodity values after imputation: {missing_after}")

yahoo_spot_df[commodity_cols] = yahoo_spot_df[commodity_cols].round(2)
print("Rounded commodity values to 2 decimals")

# Convert date
yahoo_spot_df["Date"] = yahoo_spot_df["Date"].dt.strftime("%d-%m-%Y")

# Save cleaned data
print("\nSaving cleaned datasets...")
yahoo_spot_df.to_csv("../../Data/Final Data/yahoo_spot_cleaned.csv", index=False, sep=",")
print("Saved: Data/Final Data/yahoo_spot_cleaned.csv")
