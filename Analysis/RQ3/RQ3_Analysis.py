"""RQ3: How does the relationship between commodity prices and used car values vary across popular car brands in Switzerland? We will segment
our analysis by brand to determine whether luxury manufacturers, producers, or specific market segments exhibit different sensitivities
to raw material cost pressures."""
# python3 -m pip install dtale
import pandas as pd
import os
from pathlib import Path
import matplotlib.pyplot as plt
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

# ----- Data cleansing pipeline: harmonise Autoscout listings and commodity data before analysis -----
    
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

# step1: aggregate average price by brands & months, then merge with commodity avg monthly prices columns
if 'merged_df' in locals(): # make sure that the merged_df is loaded
    commodity_cols = [col for col in merged_df.columns if col.endswith('_Monthly_Avg')]

    brand_month_summary = (
        merged_df.groupby(['brand', 'Month'], as_index=False)
                 .agg(
                     price_chf_mean=('price_chf', 'mean'),
                     price_chf_median=('price_chf', 'median'),
                     listing_count=('price_chf', 'size'),
                     # count how many brands there are, to pick those with enough months.
                     mileage_mean=('mileage', 'mean'),
                     engine_power_hp_mean=('engine_power_hp', 'mean'),
                     consumption_l_per_100km_mean=('consumption_l_per_100km', 'mean')
                 )
    )

    brand_month_summary = brand_month_summary.merge(
        merged_df[['Month'] + commodity_cols].drop_duplicates(), 
        # builds a table that holds one row per month with the commodity monthly-average columns.
        on='Month',
        how='left'
    )

    brand_month_summary['price_chf_mean'] = brand_month_summary['price_chf_mean'].round(0)
    brand_month_summary['price_chf_median'] = brand_month_summary['price_chf_median'].round(0)
    brand_month_summary['mileage_mean'] = brand_month_summary['mileage_mean'].round(0)
    brand_month_summary['engine_power_hp_mean'] = brand_month_summary['engine_power_hp_mean'].round(0)
    brand_month_summary['consumption_l_per_100km_mean'] = brand_month_summary['consumption_l_per_100km_mean'].round(2)

    print("\nBrand–Month summary preview:")
    print(brand_month_summary.head())

    top_brands = (
        brand_month_summary.groupby('brand')['listing_count']
                           .sum()
                           .sort_values(ascending=False)
                           .head(10)
    )
    print("\nTop brands by total listings:")
    print(top_brands)
else:
    print("merged_df not found. Run the merge cell first.")

# Brand monthly data coverage summary, have a look first
brand_coverage = (
    brand_month_summary.assign(
        has_all_commodities=brand_month_summary[commodity_cols].notna().all(axis=1)
    )
    # above adds a new column, has_all_commodities, to every brand–month row. That column is True when all the commodity monthly-average columns are present (non-missing) for that row, and False otherwise
    .groupby('brand')
    .agg(
        listing_count_total=('listing_count', 'sum'),
        months_total=('Month', 'nunique'),
        months_with_commodities=('has_all_commodities', 'sum'),
        first_month=('Month', 'min'),
        last_month=('Month', 'max')
    )
    .sort_values('listing_count_total', ascending=False)
)

print("\nBrand coverage summary:")
print(brand_coverage.head(20))

# step2: limit to window where commodity monthly averages exist consistently (≈2020 onwards)
analysis_window = brand_month_summary[brand_month_summary['Month'] >= '2020-01'].copy()

analysis_window_coverage = (
    analysis_window.assign(
        has_all_commodities=analysis_window[commodity_cols].notna().all(axis=1)
    ) # adds a new boolean column for each brand–month row, non-missing, the flag is True, otherwise False
    .groupby('brand')
    .agg(
        listing_count_total=('listing_count', 'sum'),
        months_total=('Month', 'nunique'),
        months_with_commodities=('has_all_commodities', 'sum'),
        first_month=('Month', 'min'),
        last_month=('Month', 'max')
    )
    .sort_values('listing_count_total', ascending=False)
)

print("\nPost-2020 brand coverage summary:")
print(analysis_window_coverage.head(20))

# result: seems that only starting from 2020 01 commodity prices are available

#%% Cell 5 Brand vs Commodity Exploration
if 'analysis_window' in locals() and not analysis_window.empty:
    min_months_required = 10
    max_brands_to_plot = 12
    coverage_sorted = analysis_window_coverage.sort_values('months_with_commodities', ascending=False)
    candidate_brands = coverage_sorted[coverage_sorted['months_with_commodities'] >= min_months_required].index.tolist()
    candidate_brands = candidate_brands[:max_brands_to_plot]  # keep charts readable

    if candidate_brands:
        print(
            f"\nBrands used for plots (>= {min_months_required} months with commodities,"
            f" max {max_brands_to_plot} brands): {candidate_brands}"
        )

        selected_df = analysis_window[analysis_window['brand'].isin(candidate_brands)].copy()

        avg_price = selected_df.groupby('brand')['price_chf_mean'].mean().sort_values(ascending=False)

        fig1 = plt.figure(figsize=(10, 5))
        plt.bar(avg_price.index, avg_price.values, color='steelblue')
        plt.title('Average Monthly Car Price (Post-2020)')
        plt.ylabel('Average price (CHF)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        output_dir = script_dir / "outputs"
        output_dir.mkdir(exist_ok=True)
        fig1.savefig(output_dir / "avg_price_by_brand.png", dpi=300, bbox_inches='tight')
        print(f"Saved: {output_dir / 'avg_price_by_brand.png'}")
        plt.show()

        if commodity_cols:
            max_commodities_to_plot = 6
            for commodity in commodity_cols[:max_commodities_to_plot]:
                corr_values = []
                for brand in candidate_brands:
                    brand_rows = selected_df[selected_df['brand'] == brand].sort_values('Month')
                    correlation = brand_rows['price_chf_mean'].corr(brand_rows[commodity]) if commodity in brand_rows else None
                    corr_values.append((brand, correlation))

                corr_values = [(b, c) for b, c in corr_values if pd.notna(c)]
                if corr_values:
                    brands_corr, values_corr = zip(*corr_values)
                    fig = plt.figure(figsize=(10, 5))
                    plt.bar(brands_corr, values_corr, color='darkorange')
                    plt.axhline(0, color='black', linewidth=0.8)
                    plt.title(f'Price vs {commodity} correlation')
                    plt.ylabel('Pearson correlation')
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    commodity_clean = commodity.replace('_Monthly_Avg', '').replace('_Spot', '')
                    fig.savefig(output_dir / f"correlation_{commodity_clean}.png", dpi=300, bbox_inches='tight')
                    print(f"Saved: {output_dir / f'correlation_{commodity_clean}.png'}")
                    plt.show()
                else:
                    print(f"Correlation could not be computed for {commodity} (insufficient variation).")

            corr_rows = []
            for brand in candidate_brands:
                brand_rows = selected_df[selected_df['brand'] == brand].sort_values('Month')
                row = {'brand': brand}
                for commodity in commodity_cols:
                    if commodity in selected_df.columns:
                        row[commodity] = brand_rows['price_chf_mean'].corr(brand_rows[commodity])
                corr_rows.append(row)

            corr_matrix = pd.DataFrame(corr_rows).set_index('brand')
            print("\nBrand vs commodity correlations (Pearson):")
            print(corr_matrix)

            if not corr_matrix.empty:
                base_width = 1 + 0.6 * len(corr_matrix.columns)
                base_height = 0.6 * len(corr_matrix.index) + 2
                width = max(10, 0.9 * base_width)
                height = max(5, 1.1 * base_height)
                fig_heatmap = plt.figure(figsize=(width, height))
                plt.imshow(corr_matrix.values, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
                plt.colorbar(label='Correlation')
                plt.xticks(range(len(corr_matrix.columns)), corr_matrix.columns, rotation=45, ha='right')
                plt.yticks(range(len(corr_matrix.index)), corr_matrix.index)
                plt.title('Price vs Commodity Correlation Matrix')
                plt.tight_layout()
                fig_heatmap.savefig(output_dir / "correlation_matrix_heatmap.png", dpi=300, bbox_inches='tight')
                print(f"Saved: {output_dir / 'correlation_matrix_heatmap.png'}")
                plt.show()
        else:
            print("No commodity columns found for plotting.")
    else:
        print(f"No brands meet the >= {min_months_required} months threshold for commodity coverage.")
else:
    print("analysis_window not available. Run previous cells first.")

# Conclusions
"""
Main Findings
1. Brand-Specific Sensitivities Exist
The correlation matrix reveals that commodity price relationships are not uniform across brands:

Volvo shows the strongest positive correlations with multiple commodities (Copper: 0.52, Cobalt: 0.38), suggesting its used car prices track raw material costs more closely—likely due to premium positioning and EV/hybrid component mix.
Porsche exhibits moderate positive correlations with Nickel (0.34) and other metals, consistent with luxury manufacturing using specialized materials.
European mass-market brands (VW, Audi, Skoda) show minimal-to-moderate positive correlations with Copper and Steel, indicating minimal to moderate sensitivity to industrial metal prices.

2. Negative Correlations in Asian Brands
Toyota and Cupra display negative correlations across most commodities (Toyota: WTI -0.45, Nickel -0.39; Cupra: WTI -0.46, Cobalt -0.56).
This suggests their used car prices moved inversely to commodity trends during 2020-2025, possibly due to:
Different supply chain structures
Pricing strategies that absorb cost fluctuations
Product mix less dependent on volatile raw materials
Market positioning focused on value/reliability over premium materials

3. Luxury vs. Mass-Market Divergence
Premium brands (Mercedes-Benz, BMW, Porsche) show mixed but generally weak correlations, suggesting their pricing power and brand equity may buffer them from direct commodity cost pass-through.
Mass-market European brands show slightly stronger positive ties to industrial metals, indicating more direct exposure to manufacturing cost pressures.

4. Commodity-Specific Patterns
Copper emerges as the most consistently positive correlate across European brands, reflecting its widespread use in electrical systems and wiring.
WTI (oil) shows negative correlations for several brands, possibly because higher fuel costs reduce demand for ICE vehicles, depressing their resale values.
Battery metals (Lithium, Cobalt, Nickel) show varied patterns—strongest for brands with significant EV/hybrid portfolios (Volvo, Porsche).

5. Limitations in RQ3 Conclusion
Reliable commodity data only spans 2020-2025 (56 months max per brand), limiting ability to detect long-term trends or cyclical patterns.
Time-series decomposition wasn't viable due to short series, so seasonal effects and structural breaks remain unexplored.
Summary Statement for RQ3
The relationship between commodity prices and used car values varies significantly across Swiss car brands. European premium and mass-market brands show mild-to-moderate positive correlations with industrial metals (especially Copper), while Asian brands exhibit negative correlations, suggesting different cost structures and pricing strategies. Volvo demonstrates the strongest sensitivity to battery metals, aligning with its electrification strategy. However, the post-2020 data window and brand-level aggregation limit deeper causal inference—brand equity, model mix, and market positioning appear to mediate commodity price impacts more than direct cost pass-through.
"""

