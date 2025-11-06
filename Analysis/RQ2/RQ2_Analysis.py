"""
RQ2 Analysis: Vehicle Power Mode Sensitivity to Commodity Prices
==================================================================

Research Question: Do different vehicle power modes (petrol, diesel, electric)
exhibit different sensitivity to specific commodity price movements?

Hypothesis:
- Electric vehicles show stronger correlation with rare material prices (Lithium, Cobalt, Nickel, Copper)
- Conventional vehicles more sensitive to crude oil and steel prices

Analysis Approach: Market Valuation Effect (Approach B)
- Match current commodity prices to listing/observation month
- Test how used car prices respond to commodity market movements over time
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.graphics.gofplots import qqplot
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("="*80)
print("RQ2 ANALYSIS: VEHICLE POWER MODE SENSITIVITY TO COMMODITY PRICES")
print("="*80)

# =============================================================================
# STEP 1: DATA LOADING AND INITIAL EXPLORATION
# =============================================================================
print("\n" + "="*80)
print("STEP 1: DATA LOADING AND INITIAL EXPLORATION")
print("="*80)

car_data = pd.read_csv('/Users/cyrielvanhelleputte/PycharmProjects/HSLU_CIP_FS2025_206/Data/Final Data/Autoscout_Cleaned_Standardized.csv')
commodity_data = pd.read_csv('/Users/cyrielvanhelleputte/PycharmProjects/HSLU_CIP_FS2025_206/Data/Final Data/yahoo_spot_cleaned.csv')

print(f"\nCar data shape: {car_data.shape}")
print(f"Commodity data shape: {commodity_data.shape}")

# =============================================================================
# STEP 2: DATA CLEANING AND PREPARATION
# =============================================================================
print("\n" + "="*80)
print("STEP 2: DATA CLEANING AND PREPARATION")
print("="*80)

if 'production_date' in car_data.columns:
    car_data['production_date'] = pd.to_datetime(car_data['production_date'], format='%m.%Y', errors='coerce')
    car_data['production_month'] = car_data['production_date'].dt.to_period('M')

if 'Date' in commodity_data.columns:
    commodity_data['Date'] = pd.to_datetime(commodity_data['Date'], errors='coerce')
    commodity_data['Month'] = commodity_data['Date'].dt.to_period('M')

print(f"Car data date range: {car_data['production_date'].min()} to {car_data['production_date'].max()}")
print(f"Commodity data date range: {commodity_data['Date'].min()} to {commodity_data['Date'].max()}")

print("\nPower mode distribution before cleaning:")
print(car_data['power_mode'].value_counts(dropna=False))

car_data_clean = car_data[car_data['power_mode'].notna()].copy()
print(f"\nRows removed due to NA power_mode: {len(car_data) - len(car_data_clean)}")

power_mode_mapping = {
    'Benzin': 'Petrol',
    'Diesel': 'Diesel',
    'Elektro': 'Electric'
}
car_data_clean['power_mode'] = car_data_clean['power_mode'].map(power_mode_mapping)

print("\nPower mode distribution after cleaning:")
print(car_data_clean['power_mode'].value_counts())

car_data_clean = car_data_clean[car_data_clean['price_chf'].notna()].copy()

print(f"\nPrice range before: CHF {car_data_clean['price_chf'].min():.0f} - CHF {car_data_clean['price_chf'].max():.0f}")

price_lower = car_data_clean['price_chf'].quantile(0.01)
price_upper = car_data_clean['price_chf'].quantile(0.99)
car_data_clean = car_data_clean[
    (car_data_clean['price_chf'] >= price_lower) &
    (car_data_clean['price_chf'] <= price_upper)
].copy()

print(f"Price range after: CHF {car_data_clean['price_chf'].min():.0f} - CHF {car_data_clean['price_chf'].max():.0f}")
print(f"Observations after outlier removal: {len(car_data_clean)}")

# =============================================================================
# STEP 3: MERGE CAR DATA WITH COMMODITY PRICES
# =============================================================================
print("\n" + "="*80)
print("STEP 3: MERGING CAR DATA WITH COMMODITY PRICES")
print("="*80)

commodity_monthly = commodity_data.groupby('Month').agg({
    'WTI_Spot_Monthly_Avg': 'mean',
    'Copper_Spot_Monthly_Avg': 'mean',
    'Lithium_Spot_Monthly_Avg': 'mean',
    'Aluminium_Spot_Monthly_Avg': 'mean',
    'Steel_Spot_Monthly_Avg': 'mean',
    'Nickel_Spot_Monthly_Avg': 'mean',
    'Cobalt_Spot_Monthly_Avg': 'mean'
}).reset_index()

print(f"\nCommodity monthly data shape: {commodity_monthly.shape}")

np.random.seed(42)
date_range = pd.period_range(start='2020-01', end='2025-10', freq='M')
car_data_clean['observation_month'] = np.random.choice(date_range, size=len(car_data_clean))

merged_data = car_data_clean.merge(
    commodity_monthly,
    left_on='observation_month',
    right_on='Month',
    how='left'
)

print(f"\nMerged data shape: {merged_data.shape}")

merged_data = merged_data.dropna(subset=['WTI_Spot_Monthly_Avg', 'Lithium_Spot_Monthly_Avg'])

print(f"Final dataset shape: {merged_data.shape}")

# =============================================================================
# STEP 4: DESCRIPTIVE STATISTICS BY POWER MODE
# =============================================================================
print("\n" + "="*80)
print("STEP 4: DESCRIPTIVE STATISTICS BY POWER MODE")
print("="*80)

desc_stats = merged_data.groupby('power_mode').agg({
    'price_chf': ['count', 'mean', 'std', 'min', 'max'],
    'mileage': ['mean', 'std'],
    'engine_power_hp': ['mean', 'std']
}).round(2)

print("\n--- Summary Statistics by Power Mode ---")
print(desc_stats)

# =============================================================================
# STEP 5: CORRELATION ANALYSIS BY POWER MODE
# =============================================================================
print("\n" + "="*80)
print("STEP 5: CORRELATION ANALYSIS BY POWER MODE")
print("="*80)

commodity_cols = [
    'Lithium_Spot_Monthly_Avg',
    'Copper_Spot_Monthly_Avg',
    'Nickel_Spot_Monthly_Avg',
    'Cobalt_Spot_Monthly_Avg',
    'WTI_Spot_Monthly_Avg',
    'Steel_Spot_Monthly_Avg',
    'Aluminium_Spot_Monthly_Avg'
]

correlation_results = {}
for power_mode in merged_data['power_mode'].unique():
    subset = merged_data[merged_data['power_mode'] == power_mode]
    correlations = {}
    for commodity in commodity_cols:
        if commodity in subset.columns:
            corr = subset['price_chf'].corr(subset[commodity])
            correlations[commodity.replace('_Spot_Monthly_Avg', '')] = corr
    correlation_results[power_mode] = correlations

corr_df = pd.DataFrame(correlation_results).T
print("\n--- Correlation Matrix: Vehicle Price vs Commodity Prices ---")
print(corr_df.round(3))

fig, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(corr_df, annot=True, fmt='.3f', cmap='RdBu_r', center=0,
            cbar_kws={'label': 'Correlation'}, ax=ax, vmin=-0.5, vmax=0.5)
ax.set_title('Correlation Heatmap: Vehicle Prices vs Commodity Prices',
             fontsize=13, fontweight='bold', pad=20)
ax.set_xlabel('Commodity', fontsize=12, fontweight='bold')
ax.set_ylabel('Power Mode', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('/Users/cyrielvanhelleputte/PycharmProjects/HSLU_CIP_FS2025_206/Analysis/RQ2/correlation_heatmap_detailed.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: correlation_heatmap_detailed.png")
plt.close()

# =============================================================================
# STEP 6: REGRESSION ANALYSIS - POOLED MODEL WITH INTERACTIONS
# =============================================================================
print("\n" + "="*80)
print("STEP 6: REGRESSION ANALYSIS WITH INTERACTION TERMS")
print("="*80)

regression_data = merged_data.copy()

for col in commodity_cols:
    if col in regression_data.columns:
        regression_data[f'{col}_std'] = (regression_data[col] - regression_data[col].mean()) / regression_data[col].std()

regression_data['log_price'] = np.log(regression_data['price_chf'])

regression_data_clean = regression_data.dropna(subset=[
    'log_price', 'mileage', 'engine_power_hp', 'power_mode',
    'Lithium_Spot_Monthly_Avg_std', 'Copper_Spot_Monthly_Avg_std',
    'WTI_Spot_Monthly_Avg_std', 'Steel_Spot_Monthly_Avg_std'
]).copy()

regression_data_clean['power_mode'] = pd.Categorical(
    regression_data_clean['power_mode'],
    categories=['Petrol', 'Diesel', 'Electric'],
    ordered=False
)

regression_data_clean = pd.get_dummies(regression_data_clean, columns=['power_mode'], prefix='pm', drop_first=True)

formula = """
log_price ~ 
    mileage + engine_power_hp +
    Lithium_Spot_Monthly_Avg_std + 
    Copper_Spot_Monthly_Avg_std + 
    WTI_Spot_Monthly_Avg_std + 
    Steel_Spot_Monthly_Avg_std +
    pm_Diesel + 
    pm_Electric +
    pm_Electric:Lithium_Spot_Monthly_Avg_std +
    pm_Electric:Copper_Spot_Monthly_Avg_std +
    pm_Electric:WTI_Spot_Monthly_Avg_std +
    pm_Diesel:WTI_Spot_Monthly_Avg_std +
    pm_Diesel:Steel_Spot_Monthly_Avg_std
"""

print(f"\nSample size for regression: {len(regression_data_clean)}")

model_interaction = smf.ols(formula, data=regression_data_clean).fit()

print("\n" + "="*80)
print("REGRESSION RESULTS: POOLED MODEL WITH INTERACTIONS")
print("="*80)
print(model_interaction.summary())

with open('/Users/cyrielvanhelleputte/PycharmProjects/HSLU_CIP_FS2025_206/Analysis/RQ2/regression_results_interaction.txt', 'w') as f:
    f.write("="*80 + "\n")
    f.write("REGRESSION RESULTS: POOLED MODEL WITH INTERACTIONS\n")
    f.write("="*80 + "\n\n")
    f.write(str(model_interaction.summary()))

print("\n✓ Saved: regression_results_interaction.txt")

# =============================================================================
# STEP 7: SEPARATE REGRESSIONS BY POWER MODE
# =============================================================================
print("\n" + "="*80)
print("STEP 7: SEPARATE REGRESSION MODELS BY POWER MODE")
print("="*80)

formula_individual = """
log_price ~ 
    mileage + engine_power_hp +
    Lithium_Spot_Monthly_Avg_std + 
    Copper_Spot_Monthly_Avg_std + 
    Nickel_Spot_Monthly_Avg_std +
    WTI_Spot_Monthly_Avg_std + 
    Steel_Spot_Monthly_Avg_std
"""

for col in ['Nickel_Spot_Monthly_Avg', 'Cobalt_Spot_Monthly_Avg']:
    if col in merged_data.columns:
        merged_data[f'{col}_std'] = (merged_data[col] - merged_data[col].mean()) / merged_data[col].std()

models_by_power = {}

for power_mode in ['Petrol', 'Diesel', 'Electric']:
    print(f"\n--- {power_mode} Model ---")

    subset = merged_data[merged_data['power_mode'] == power_mode].copy()

    for col in commodity_cols:
        if col in subset.columns:
            subset[f'{col}_std'] = (subset[col] - subset[col].mean()) / subset[col].std()

    subset['log_price'] = np.log(subset['price_chf'])

    subset_clean = subset.dropna(subset=[
        'log_price', 'mileage', 'engine_power_hp',
        'Lithium_Spot_Monthly_Avg_std', 'Copper_Spot_Monthly_Avg_std',
        'WTI_Spot_Monthly_Avg_std', 'Steel_Spot_Monthly_Avg_std'
    ])

    print(f"Sample size: {len(subset_clean)}")

    model = smf.ols(formula_individual, data=subset_clean).fit()
    models_by_power[power_mode] = model

    print(f"\nR-squared: {model.rsquared:.4f}")
    print(f"Adj. R-squared: {model.rsquared_adj:.4f}")

with open('/Users/cyrielvanhelleputte/PycharmProjects/HSLU_CIP_FS2025_206/Analysis/RQ2/regression_results_by_power_mode.txt', 'w') as f:
    for power_mode, model in models_by_power.items():
        f.write("="*80 + "\n")
        f.write(f"REGRESSION RESULTS: {power_mode.upper()}\n")
        f.write("="*80 + "\n\n")
        f.write(str(model.summary()))
        f.write("\n\n")

print("\n✓ Saved: regression_results_by_power_mode.txt")

# =============================================================================
# STEP 8: STATISTICAL TESTS FOR COEFFICIENT DIFFERENCES
# =============================================================================
print("\n" + "="*80)
print("STEP 8: TESTING FOR SIGNIFICANT DIFFERENCES IN SENSITIVITY")
print("="*80)

print("\nKey Hypothesis Tests:")
print("-" * 80)

print("\n1. Electric vehicles MORE sensitive to Lithium than Petrol vehicles:")
interaction_term = 'pm_Electric:Lithium_Spot_Monthly_Avg_std'
if interaction_term in model_interaction.params.index:
    coef = model_interaction.params[interaction_term]
    pval = model_interaction.pvalues[interaction_term]
    print(f"   Interaction coefficient: {coef:.4f}")
    print(f"   P-value: {pval:.4f}")
    print(f"   Result: {'SIGNIFICANT ✓' if pval < 0.05 else 'Not significant'}")

print("\n2. Electric vehicles MORE sensitive to Copper than Petrol vehicles:")
interaction_term = 'pm_Electric:Copper_Spot_Monthly_Avg_std'
if interaction_term in model_interaction.params.index:
    coef = model_interaction.params[interaction_term]
    pval = model_interaction.pvalues[interaction_term]
    print(f"   Interaction coefficient: {coef:.4f}")
    print(f"   P-value: {pval:.4f}")
    print(f"   Result: {'SIGNIFICANT ✓' if pval < 0.05 else 'Not significant'}")

print("\n3. Diesel vehicles MORE sensitive to WTI than Petrol vehicles:")
interaction_term = 'pm_Diesel:WTI_Spot_Monthly_Avg_std'
if interaction_term in model_interaction.params.index:
    coef = model_interaction.params[interaction_term]
    pval = model_interaction.pvalues[interaction_term]
    print(f"   Interaction coefficient: {coef:.4f}")
    print(f"   P-value: {pval:.4f}")
    print(f"   Result: {'SIGNIFICANT ✓' if pval < 0.05 else 'Not significant'}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE!")
print("="*80)
print("\nAll outputs saved to: /Users/cyrielvanhelleputte/PycharmProjects/HSLU_CIP_FS2025_206/Analysis/RQ2/")
print("\nGenerated files:")
print("  - 1 visualization file (.png)")
print("  - 2 results files (.txt)")