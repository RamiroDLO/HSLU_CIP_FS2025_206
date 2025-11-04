"""RQ3: How does the relationship between commodity prices and used car values vary across popular car brands in Switzerland? We will segment
our analysis by brand to determine whether luxury manufacturers, producers, or specific market segments exhibit different sensitivities
to raw material cost pressures."""
# python3 -m pip install dtale
import pandas as pd
import os
from pathlib import Path
import dtale
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

#%% Cell 2 Imputation
if 'df1' in locals() and 'df2' in locals():
    autoscout = df1.copy() # Copy dfs to avoid modifying original dfs
    commodities = df2.copy()

# ----- when final cleaning script is finished again by Cyriel, as discussed this lunch, this temporary part can be deleted or adjusted, if missing values are all dealt with
    
    # Step 1: check missing values, general cleaning
    # coerce "Neues Fahrzeug" entries and standardize production dates
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
        if col not in autoscout.columns:
            continue
        if col == 'consumption_l_per_100km':
            continue  # handle consumption via logic below
        mean_value = autoscout[col].mean()
        if pd.notna(mean_value): # checks computed column mean isn’t NaN
            autoscout[col] = autoscout[col].fillna(mean_value)
            autoscout[col] = autoscout[col].round(0)

    consumption_col = 'consumption_l_per_100km'
    count_ev_imputed = count_model_imputed = count_brand_imputed = count_global_imputed = 0
    if consumption_col in autoscout.columns:
        original_consumption_mean = autoscout[consumption_col].mean(skipna=True)

        if 'power_mode' in autoscout.columns: # if elektro/electric, set to 0
            ev_mask = autoscout['power_mode'].astype(str).str.lower().str.contains('elektro|electric', na=False)
            ev_fill_mask = autoscout[consumption_col].isna() & ev_mask
            autoscout.loc[ev_fill_mask, consumption_col] = 0
            count_ev_imputed = int(ev_fill_mask.sum())

        remaining_mask = autoscout[consumption_col].isna() # if not elektro/electric, see model mean if exists
        if remaining_mask.any() and 'model' in autoscout.columns:
            model_means = autoscout.groupby('model')[consumption_col].mean()
            model_fill_values = autoscout['model'].map(model_means)
            model_fill_mask = remaining_mask & model_fill_values.notna()
            autoscout.loc[model_fill_mask, consumption_col] = model_fill_values[model_fill_mask]
            count_model_imputed = int(model_fill_mask.sum())
            remaining_mask = autoscout[consumption_col].isna()

        if remaining_mask.any() and 'brand' in autoscout.columns: # if above not possible, see brand mean if exists
            brand_means = autoscout.groupby('brand')[consumption_col].mean()
            brand_fill_values = autoscout['brand'].map(brand_means)
            brand_fill_mask = remaining_mask & brand_fill_values.notna()
            autoscout.loc[brand_fill_mask, consumption_col] = brand_fill_values[brand_fill_mask]
            count_brand_imputed = int(brand_fill_mask.sum())
            remaining_mask = autoscout[consumption_col].isna()

        if remaining_mask.any() and pd.notna(original_consumption_mean): # if above not possible, see overall mean.notna
            autoscout.loc[remaining_mask, consumption_col] = original_consumption_mean
            count_global_imputed = int(remaining_mask.sum())

        print("\nconsumption_l_per_100km imputation summary:")
        print(f"  Elektro/Electric power_mode set to 0: {count_ev_imputed}")
        print(f"  Filled from model mean: {count_model_imputed}")
        print(f"  Filled from brand mean: {count_brand_imputed}")
        print(f"  Filled from overall mean: {count_global_imputed}")

        autoscout[consumption_col] = autoscout[consumption_col].round(2)

    autoscout_missing_after_numeric = autoscout.isna().sum()
    print("\nAutoscout missing values (after filling continuous columns):")
    print(autoscout_missing_after_numeric)

    # Impute categorical columns missing value (power_mode, transmission) using model majority, if not possible falling back to 'Unknown'
    if 'model' in autoscout.columns:
        for cat_col in ['power_mode', 'transmission']:
            if cat_col in autoscout.columns:
                mode_map = (
                    autoscout.dropna(subset=[cat_col])
                             .groupby('model')[cat_col]
                             .agg(lambda x: x.mode().iat[0] if not x.mode().empty else pd.NA)
                )
                        # .iat is pandas’ integer-position accessor for Series/DataFrame values
                        #  In pandas, .agg() applies an aggregation function to each group produced by groupby 
                autoscout[cat_col] = autoscout[cat_col].fillna(autoscout['model'].map(mode_map))
                autoscout[cat_col] = autoscout[cat_col].fillna('Unknown')

    autoscout_missing_after_categorical = autoscout.isna().sum()
    print("\nAutoscout missing values (after categorical imputation):")
    print(autoscout_missing_after_categorical)

    # Impute missing production_date and Month using (model median, then brand median)
    if 'production_date' in autoscout.columns:
        production_missing_before = autoscout['production_date'].isna().sum()
        if production_missing_before:
            model_prod_map = (  # mapping each model to its median production date 
                autoscout.dropna(subset=['production_date'])
                         .groupby('model')['production_date']
                         .median()
            )
            model_missing_mask = autoscout['production_date'].isna()
            autoscout.loc[model_missing_mask, 'production_date'] = autoscout.loc[model_missing_mask, 'model'].map(model_prod_map)  # fetches the median date for each missing row’s model

            brand_missing_mask = autoscout['production_date'].isna()
            if brand_missing_mask.any():
                brand_prod_map = (
                    autoscout.dropna(subset=['production_date'])
                             .groupby('brand')['production_date']
                             .median()
                )
                autoscout.loc[brand_missing_mask, 'production_date'] = autoscout.loc[brand_missing_mask, 'brand'].map(brand_prod_map)

        production_missing_after = autoscout['production_date'].isna().sum()
        print(f"\nAutoscout missing production_date after hierarchical fill: {production_missing_after}")

        autoscout['Month'] = autoscout['production_date'].dt.to_period('M')

    if 'Month' in autoscout.columns:
        month_missing_before = autoscout['Month'].isna().sum()
        if month_missing_before:  # the function, how to fill in 
            month_model_map = (
                autoscout.dropna(subset=['Month'])
                         .groupby('model')['Month']
                         .agg(lambda x: x.mode().iat[0] if not x.mode().empty else pd.NaT)  # .mode() is a pandas Series method that returns the most frequent value(s) in that Series.
                        # .iat is pandas’ integer-position accessor for Series/DataFrame values
                        #  In pandas, .agg() applies an aggregation function to each group produced by groupby   
            )
            month_missing_mask = autoscout['Month'].isna()
            autoscout.loc[month_missing_mask, 'Month'] = autoscout.loc[month_missing_mask, 'model'].map(month_model_map)
            # the action of filling in with the above function

            month_missing_mask = autoscout['Month'].isna()
            if month_missing_mask.any():
                month_brand_map = (
                    autoscout.dropna(subset=['Month'])
                             .groupby('brand')['Month']
                             .agg(lambda x: x.mode().iat[0] if not x.mode().empty else pd.NaT)
                )
                autoscout.loc[month_missing_mask, 'Month'] = autoscout.loc[month_missing_mask, 'brand'].map(month_brand_map)

        autoscout['Month'] = autoscout['Month'].astype('period[M]')
        month_missing_after = autoscout['Month'].isna().sum()
        print(f"Month missing after hierarchical fill: {month_missing_after}")
# ----- when final cleaning script is finished again by Cyriel, as discussed this lunch, this temporary part can be deleted or adjusted, if missing values are all dealt with

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

    # keep the existing Monthly price for each commodity only
    monthly_cols = [col for col in commodities.columns if col.endswith('_Monthly_Avg')]
    commodities_monthly = (
    commodities.dropna(subset=['Month']) # remove rows with missing months
               .drop_duplicates(subset=['Month']) # keeps the first occurrence for each month
               [['Month'] + monthly_cols]
)
    # Step 3: merge on monthly column
    merged_df = autoscout.merge(commodities_monthly, on='Month', how='left', suffixes=('_car', '_commodity'))
    # output csv file
    output_path = data_dir / "Final_Merged_Data_RQ3.csv"
    merged_df.to_csv(output_path, index=False)
    print(f"\nMerged dataset saved to: {output_path}")

    print("\nMerged dataset preview:")
    print(merged_df.head())
    print("\nMonth dtype:", merged_df['Month'].dtype)
    print(f"\nMerged dataset shape: {merged_df.shape}")
else:
    print("Dataframes could not be prepared for merging. Ensure data was loaded successfully above.")

#%% Cell 3 Data Inspection(visually dtale)
# to be done, didnt work with dtale this time, unstable local host browser connection

#%% Cell 4 relationship between commodity prices and used car values across brands
# Aggregate car prices (mean/median) by brand and Month, then visualise trends alongside commodity curves to spot brand-specific sensitivities.