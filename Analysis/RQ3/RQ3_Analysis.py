"""RQ3: How does the relationship between commodity prices and used car values vary across popular car brands in Switzerland? We will segment
our analysis by brand to determine whether luxury manufacturers, producers, or specific market segments exhibit different sensitivities
to raw material cost pressures."""

import pandas as pd
import os
from pathlib import Path
#%% Cell 1 Load Data
# Get script location
script_dir = Path(__file__).parent

# Relative paths from the script location
data_dir = script_dir.parent.parent / "Data" / "Final Data"
path_autoscout = data_dir / "Autoscout_Cleaned_Standardized.csv"
path_yahoo = data_dir / "yahoo_spot_cleaned.csv"

try:
    # Load the data
    df1 = pd.read_csv(path_autoscout)
    df2 = pd.read_csv(path_yahoo)
    
    # Data inspection
    print("Autoscout Data (first 5 rows):")
    print(df1.head())
    print("\nYahoo Commodity Data (first 5 rows):")
    print(df2.head())
    
except FileNotFoundError as e:
    print(f"Error: {e}")
    print(f"File not found, current working directory: {os.getcwd()}")
    print(f"Looking for files at:")
    print(f"- {path_autoscout.absolute()}")
    print(f"- {path_yahoo.absolute()}")

#%% Cell 2 Data Merge, Inspection
if 'df1' in locals() and 'df2' in locals():
    autoscout = df1.copy() # Copy dfs to avoid modifying original dfs
    commodities = df2.copy()
# ----------- when final cleaning script is finished again by Cyriel as discussed this lunch, this temporary part can be deleted or adjusted, if missing values are all dealt with
    # Step 1: coerce "Neues Fahrzeug" entries and standardize production dates
    autoscout['production_date'] = autoscout['production_date'].replace(
        {'Neues Fahrzeug': '10.2025'}
    )
    autoscout['production_date'] = pd.to_datetime(autoscout['production_date'], format='%m.%Y', errors='coerce')   # Any value that doesn’t match (e.g., still “Neues Fahrzeug”) becomes NaT because of errors='coerce'
    autoscout['Month'] = autoscout['production_date'].dt.to_period('M') # converts datetime in the column to a pandas Period representing calendar month 

    # Identify continuous columns and coerce to numeric
    autoscout_continuous = [
        'price_chf',
        'mileage',
        'engine_power_hp',
        'consumption_l_per_100km'
    ]
    for col in autoscout_continuous:
        if col in autoscout.columns:
            autoscout[col] = pd.to_numeric(autoscout[col], errors='coerce')
    # Check missing values in all columns
    autoscout_missing_before = autoscout.isna().sum()
    print("\nAutoscout missing values (before filling continuous columns):")
    print(autoscout_missing_before)

    for col in autoscout_continuous:
        if col in autoscout.columns:
            mean_value = autoscout[col].mean()
            if pd.notna(mean_value): # checks that the computed column mean isn’t NaN
                autoscout[col] = autoscout[col].fillna(mean_value)

    autoscout_missing_after = autoscout.isna().sum()
    print("\nAutoscout missing values (after filling continuous columns):")
    print(autoscout_missing_after)

    # Step 2: prepare commodity data with consistent month keys
    commodities['Date'] = pd.to_datetime(commodities['Date'], errors='coerce')
    commodities['Month'] = pd.to_datetime(commodities['Month'], format='%m-%Y', errors='coerce')
    # In case of missing months, fill again with available daily dates
    missing_month_mask = commodities['Month'].isna() & commodities['Date'].notna() # flags rows where the formatted Month column is missing (NaT) but the daily Date value exists.
    commodities.loc[missing_month_mask, 'Month'] = commodities.loc[missing_month_mask, 'Date'] # then fills those gaps by copying over the available Date. (The next line converts both to the YYYY-MM string.)

    commodities['Month'] = commodities['Month'].dt.to_period('M') # converts datetime in the column to a pandas Period representing calendar month  

    commodities_missing_before = commodities.isna().sum()
    print("\nCommodity data missing values (before filling continuous columns):")
    print(commodities_missing_before)

    commodities_numeric = commodities.select_dtypes(include='number').columns
    for col in commodities_numeric:
        mean_value = commodities[col].mean()
        if pd.notna(mean_value):
            commodities[col] = commodities[col].fillna(mean_value)

    commodities_missing_after = commodities.isna().sum()
    print("\nCommodity data missing values (after filling continuous columns):")
    print(commodities_missing_after)

    commodities = commodities.dropna(subset=['Month'])
    commodities_monthly = commodities.groupby('Month', as_index=False)[commodities_numeric].mean()

    # Step 3: merge on standardized month column
    merged_df = autoscout.merge(commodities_monthly, on='Month', how='left', suffixes=('_car', '_commodity'))

    print("\nMerged dataset preview:")
    print(merged_df.head())
    print("\nMonth dtype:", merged_df['Month'].dtype)
    print(f"\nMerged dataset shape: {merged_df.shape}")
else:
    print("Dataframes could not be prepared for merging. Ensure data was loaded successfully above.")
