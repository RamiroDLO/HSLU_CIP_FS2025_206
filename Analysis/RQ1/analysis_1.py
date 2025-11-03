"""
RQ1: Correlation Analysis - Used Car Prices vs Commodity Indices
Time series analysis to compare relationship between used car prices 
and  commodity costs ( crude oil, steel, aluminum, copper, nickel, cobalt)
"""

import pandas as pd
import os
path_autoscout = "project_scraping_CIP_analysis_car_commodity_price/Data/Final Data/autoscout_cleaned.csv"
path_yahoo = "project_scraping_CIP_analysis_car_commodity_price/Data/Final Data/yahoo_spot_cleaned.csv"


df1 = pd.read_csv(path_autoscout)
df2 = pd.read_csv(path_yahoo)

print(df1, "\n" ,  df2)

print("="*80)
print("RQ1: COMMODITY PRICES vs USED CAR PRICES CORRELATION ANALYSIS")
print("="*80)

# ============================================================================
# 1. LOAD DATA
# ============================================================================
print("\n[1] Loading datasets...")

autoscout_df = pd.read_csv(AUTOSCOUT_PATH, sep=";")
yahoo_df = pd.read_csv(YAHOO_PATH, sep=",")

print(f"   AutoScout: {len(autoscout_df):,} cars")
print(f"   Yahoo Commodities: {len(yahoo_df):,} days")

# ============================================================================
# 2. PREPARE AUTOSCOUT DATA
# ============================================================================
print("\n[2] Preparing AutoScout data...")

# Parse production date (format: MM.YYYY)
autoscout_df['production_date_str'] = autoscout_df['production_date'].astype(str)
autoscout_df['production_month'] = autoscout_df['production_date_str'].str.split('.').str[0].astype(float)
autoscout_df['production_year'] = autoscout_df['production_date_str'].str.split('.').str[1].astype(float)

# Create production date
autoscout_df['production_date_parsed'] = pd.to_datetime(
    autoscout_df['production_year'].astype(int).astype(str) + '-' + 
    autoscout_df['production_month'].astype(int).astype(str) + '-01',
    errors='coerce'
)

# Convert price to numeric
autoscout_df['price'] = pd.to_numeric(autoscout_df['price'], errors='coerce')
autoscout_df['mileage'] = pd.to_numeric(autoscout_df['mileage'], errors='coerce')

# Remove invalid data
autoscout_df = autoscout_df.dropna(subset=['production_date_parsed', 'price'])
autoscout_df = autoscout_df[autoscout_df['price'] > 0]

# Calculate vehicle age
current_date = pd.Timestamp.now()
autoscout_df['vehicle_age_years'] = (
    (current_date - autoscout_df['production_date_parsed']).dt.days / 365.25
)

print(f"   Valid cars after cleaning: {len(autoscout_df):,}")
print(f"   Date range: {autoscout_df['production_date_parsed'].min()} to {autoscout_df['production_date_parsed'].max()}")

# ============================================================================
# 3. PREPARE COMMODITY DATA
# ============================================================================
print("\n[3] Preparing commodity data...")

yahoo_df['Date'] = pd.to_datetime(yahoo_df['Date'])
yahoo_df = yahoo_df.sort_values('Date')

# Define automotive materials (excluding Lithium, Nickel, Cobalt)
automotive_commodities = {
    'WTI_Spot': 0.30,        # Crude oil - 30% (fuel, plastics, transportation)
    'Steel_Spot': 0.35,      # Steel - 35% (body, frame, structure)
    'Aluminium_Spot': 0.25,  # Aluminum - 25% (engine, wheels, body panels)
    'Copper_Spot': 0.10      # Copper - 10% (wiring, electronics)
}

print(f"\n   Composite Index Weights:")
for commodity, weight in automotive_commodities.items():
    print(f"      {commodity:20s}: {weight*100:.0f}%")

# Create indexed values (Base 100 at first date)
yahoo_indexed = yahoo_df.copy()
for commodity in automotive_commodities.keys():
    first_valid = yahoo_df[commodity].dropna().iloc[0]
    yahoo_indexed[f'{commodity}_indexed'] = (yahoo_df[commodity] / first_valid) * 100

# Calculate weighted composite index
yahoo_indexed['Composite_Index'] = sum(
    yahoo_indexed[f'{commodity}_indexed'] * weight 
    for commodity, weight in automotive_commodities.items()
)

# Resample to monthly
yahoo_monthly = yahoo_indexed.set_index('Date').resample('MS').agg({
    'Composite_Index': 'mean',
    'WTI_Spot': 'mean',
    'Steel_Spot': 'mean',
    'Aluminium_Spot': 'mean',
    'Copper_Spot': 'mean'
}).reset_index()

yahoo_monthly.rename(columns={'Date': 'Month'}, inplace=True)

print(f"   Monthly commodity data: {len(yahoo_monthly)} months")

# ============================================================================
# 4. AGGREGATE CAR PRICES BY PRODUCTION MONTH
# ============================================================================
print("\n[4] Aggregating car prices by production month...")

# Group by production month
autoscout_df['production_month_date'] = autoscout_df['production_date_parsed'].dt.to_period('M').dt.to_timestamp()

monthly_cars = autoscout_df.groupby('production_month_date').agg({
    'price': ['median', 'mean', 'count'],
    'vehicle_age_years': 'mean',
    'mileage': 'mean'
}).reset_index()

monthly_cars.columns = ['Month', 'median_price', 'mean_price', 'car_count', 'avg_age', 'avg_mileage']

print(f"   Monthly aggregation: {len(monthly_cars)} months with data")
print(f"   Total cars: {monthly_cars['car_count'].sum():,.0f}")

# ============================================================================
# 5. MERGE DATASETS
# ============================================================================
print("\n[5] Merging commodity and car price data...")

merged_df = pd.merge(
    monthly_cars,
    yahoo_monthly,
    on='Month',
    how='inner'
)

print(f"   Merged dataset: {len(merged_df)} months")
print(f"   Date range: {merged_df['Month'].min()} to {merged_df['Month'].max()}")

# Filter minimum sample size per month
min_cars_per_month = 10
merged_df = merged_df[merged_df['car_count'] >= min_cars_per_month]
print(f"   After filtering (≥{min_cars_per_month} cars/month): {len(merged_df)} months")

# ============================================================================
# 6. CORRELATION ANALYSIS
# ============================================================================
print("\n[6] Computing correlations...")
print("\n" + "="*80)
print("CORRELATION RESULTS: Median Car Price vs Commodity Indices")
print("="*80)

# Pearson correlation (linear relationship)
pearson_composite, p_pearson_composite = stats.pearsonr(
    merged_df['median_price'], 
    merged_df['Composite_Index']
)

# Spearman correlation (monotonic relationship)
spearman_composite, p_spearman_composite = stats.spearmanr(
    merged_df['median_price'], 
    merged_df['Composite_Index']
)

print(f"\nComposite Commodity Index:")
print(f"   Pearson correlation:  r = {pearson_composite:+.4f} (p = {p_pearson_composite:.4f})")
print(f"   Spearman correlation: ρ = {spearman_composite:+.4f} (p = {p_spearman_composite:.4f})")

# Individual commodities
print(f"\nIndividual Commodities:")
commodity_correlations = {}

for commodity in automotive_commodities.keys():
    pearson_r, p_pearson = stats.pearsonr(merged_df['median_price'], merged_df[commodity])
    spearman_r, p_spearman = stats.spearmanr(merged_df['median_price'], merged_df[commodity])
    
    commodity_correlations[commodity] = {
        'pearson_r': pearson_r,
        'p_pearson': p_pearson,
        'spearman_r': spearman_r,
        'p_spearman': p_spearman
    }
    
    print(f"\n   {commodity.replace('_Spot', '')}:")
    print(f"      Pearson:  r = {pearson_r:+.4f} (p = {p_pearson:.4f})")
    print(f"      Spearman: ρ = {spearman_r:+.4f} (p = {p_spearman:.4f})")

# Control variables
print(f"\nControl Variables (correlation with median price):")
age_corr, age_p = stats.pearsonr(merged_df['median_price'], merged_df['avg_age'])
mileage_corr, mileage_p = stats.pearsonr(merged_df['median_price'].dropna(), 
                                          merged_df['avg_mileage'].dropna())
print(f"   Vehicle Age:  r = {age_corr:+.4f} (p = {age_p:.4f})")
print(f"   Mileage:      r = {mileage_corr:+.4f} (p = {mileage_p:.4f})")

# ============================================================================
# 7. VISUALIZATIONS
# ============================================================================
print("\n[7] Creating visualizations...")

# Figure 1: Time Series - Dual Axis
fig, ax1 = plt.subplots(figsize=(16, 8))

color1 = 'steelblue'
ax1.set_xlabel('Production Month', fontsize=12, fontweight='bold')
ax1.set_ylabel('Median Car Price (CHF)', color=color1, fontsize=12, fontweight='bold')
ax1.plot(merged_df['Month'], merged_df['median_price'], color=color1, linewidth=2.5, 
         label='Median Car Price', marker='o', markersize=4)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, alpha=0.3)

ax2 = ax1.twinx()
color2 = 'darkred'
ax2.set_ylabel('Composite Commodity Index (Base 100)', color=color2, fontsize=12, fontweight='bold')
ax2.plot(merged_df['Month'], merged_df['Composite_Index'], color=color2, linewidth=2.5, 
         label='Commodity Index', linestyle='--', marker='s', markersize=4)
ax2.tick_params(axis='y', labelcolor=color2)

plt.title('RQ1: Used Car Prices vs Commodity Index Over Time', 
          fontsize=16, fontweight='bold', pad=20)

# Add correlation text
textstr = f'Pearson r = {pearson_composite:+.3f} (p = {p_pearson_composite:.4f})\nSpearman ρ = {spearman_composite:+.3f} (p = {p_spearman_composite:.4f})'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax1.text(0.02, 0.98, textstr, transform=ax1.transAxes, fontsize=11,
        verticalalignment='top', bbox=props)

fig.tight_layout()
plt.savefig(OUTPUT_DIR / 'RQ1_timeseries.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: RQ1_timeseries.png")
plt.close()

# Figure 2: Scatter Plot with Regression
fig, ax = plt.subplots(figsize=(12, 8))

scatter = ax.scatter(merged_df['Composite_Index'], merged_df['median_price'], 
                    c=merged_df['avg_age'], cmap='viridis', s=100, 
                    alpha=0.6, edgecolors='black', linewidth=0.5)

# Add regression line
z = np.polyfit(merged_df['Composite_Index'], merged_df['median_price'], 1)
p = np.poly1d(z)
x_line = np.linspace(merged_df['Composite_Index'].min(), merged_df['Composite_Index'].max(), 100)
ax.plot(x_line, p(x_line), "r--", linewidth=2, alpha=0.8, label=f'Linear fit: y={z[0]:.1f}x+{z[1]:.0f}')

ax.set_xlabel('Composite Commodity Index (Base 100)', fontsize=12, fontweight='bold')
ax.set_ylabel('Median Car Price (CHF)', fontsize=12, fontweight='bold')
ax.set_title('RQ1: Correlation - Car Prices vs Commodity Index\n(Color = Vehicle Age)', 
             fontsize=14, fontweight='bold', pad=20)

cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Average Vehicle Age (years)', fontsize=11)

textstr = f'Pearson r = {pearson_composite:+.4f}\nSpearman ρ = {spearman_composite:+.4f}\nn = {len(merged_df)} months'
props = dict(boxstyle='round', facecolor='lightblue', alpha=0.8)
ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=props, fontweight='bold')

ax.legend(loc='lower right', fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'RQ1_scatter.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: RQ1_scatter.png")
plt.close()

# Figure 3: Correlation Heatmap
fig, ax = plt.subplots(figsize=(10, 8))

corr_data = merged_df[['median_price', 'Composite_Index', 'WTI_Spot', 
                        'Steel_Spot', 'Aluminium_Spot', 'Copper_Spot', 
                        'avg_age', 'avg_mileage']].corr()

mask = np.triu(np.ones_like(corr_data, dtype=bool))
sns.heatmap(corr_data, mask=mask, annot=True, fmt='.3f', cmap='RdYlGn', 
            center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8},
            vmin=-1, vmax=1, ax=ax)

ax.set_title('RQ1: Correlation Matrix - Prices, Commodities & Controls', 
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'RQ1_heatmap.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: RQ1_heatmap.png")
plt.close()

# Figure 4: Individual Commodities
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
axes = axes.flatten()

commodities_plot = ['WTI_Spot', 'Steel_Spot', 'Aluminium_Spot', 'Copper_Spot']
commodity_names = ['Crude Oil (WTI)', 'Steel', 'Aluminum', 'Copper']

for idx, (commodity, name) in enumerate(zip(commodities_plot, commodity_names)):
    ax = axes[idx]
    
    corr_data = commodity_correlations[commodity]
    
    ax.scatter(merged_df[commodity], merged_df['median_price'], 
              alpha=0.6, s=80, edgecolors='black', linewidth=0.5)
    
    # Regression line
    z = np.polyfit(merged_df[commodity].dropna(), 
                   merged_df['median_price'][merged_df[commodity].notna()], 1)
    p = np.poly1d(z)
    x_line = np.linspace(merged_df[commodity].min(), merged_df[commodity].max(), 100)
    ax.plot(x_line, p(x_line), "r--", linewidth=2, alpha=0.8)
    
    ax.set_xlabel(f'{name} Price', fontsize=11, fontweight='bold')
    ax.set_ylabel('Median Car Price (CHF)', fontsize=11, fontweight='bold')
    ax.set_title(f'{name}', fontsize=12, fontweight='bold')
    
    textstr = f"r = {corr_data['pearson_r']:+.3f}\nρ = {corr_data['spearman_r']:+.3f}"
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
    
    ax.grid(True, alpha=0.3)

plt.suptitle('RQ1: Individual Commodity Correlations with Car Prices', 
             fontsize=16, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'RQ1_individual_commodities.png', dpi=300, bbox_inches='tight')
print(f"   ✓ Saved: RQ1_individual_commodities.png")
plt.close()

# ============================================================================
# 8. SAVE RESULTS
# ============================================================================
print("\n[8] Saving results...")

# Save merged dataset
merged_df.to_csv(OUTPUT_DIR / 'RQ1_merged_data.csv', index=False)
print(f"   ✓ Saved: RQ1_merged_data.csv")

# Save correlation summary
results_summary = {
    'Metric': ['Composite Index', 'WTI (Oil)', 'Steel', 'Aluminum', 'Copper', 'Vehicle Age', 'Mileage'],
    'Pearson_r': [
        pearson_composite,
        commodity_correlations['WTI_Spot']['pearson_r'],
        commodity_correlations['Steel_Spot']['pearson_r'],
        commodity_correlations['Aluminium_Spot']['pearson_r'],
        commodity_correlations['Copper_Spot']['pearson_r'],
        age_corr,
        mileage_corr
    ],
    'Pearson_p': [
        p_pearson_composite,
        commodity_correlations['WTI_Spot']['p_pearson'],
        commodity_correlations['Steel_Spot']['p_pearson'],
        commodity_correlations['Aluminium_Spot']['p_pearson'],
        commodity_correlations['Copper_Spot']['p_pearson'],
        age_p,
        mileage_p
    ],
    'Spearman_rho': [
        spearman_composite,
        commodity_correlations['WTI_Spot']['spearman_r'],
        commodity_correlations['Steel_Spot']['spearman_r'],
        commodity_correlations['Aluminium_Spot']['spearman_r'],
        commodity_correlations['Copper_Spot']['spearman_r'],
        np.nan,
        np.nan
    ],
    'Spearman_p': [
        p_spearman_composite,
        commodity_correlations['WTI_Spot']['p_spearman'],
        commodity_correlations['Steel_Spot']['p_spearman'],
        commodity_correlations['Aluminium_Spot']['p_spearman'],
        commodity_correlations['Copper_Spot']['p_spearman'],
        np.nan,
        np.nan
    ]
}

results_df = pd.DataFrame(results_summary)
results_df.to_csv(OUTPUT_DIR / 'RQ1_correlation_summary.csv', index=False)
print(f"   ✓ Saved: RQ1_correlation_summary.csv")

# ============================================================================
# 9. SUMMARY
# ============================================================================
print("\n" + "="*80)
print("RQ1 ANALYSIS COMPLETE")
print("="*80)
print(f"\nKey Findings:")
print(f"   • Sample: {len(merged_df)} months, {merged_df['car_count'].sum():,.0f} cars")
print(f"   • Composite Index Correlation: r={pearson_composite:+.3f}, ρ={spearman_composite:+.3f}")
print(f"   • Strongest commodity: {max(commodity_correlations.items(), key=lambda x: abs(x[1]['pearson_r']))[0].replace('_Spot', '')}")
print(f"\nOutputs saved to: {OUTPUT_DIR.relative_to(PROJECT_ROOT)}")
print(f"   - RQ1_timeseries.png")
print(f"   - RQ1_scatter.png")
print(f"   - RQ1_heatmap.png")
print(f"   - RQ1_individual_commodities.png")
print(f"   - RQ1_merged_data.csv")
print(f"   - RQ1_correlation_summary.csv")
print("\n✓ Analysis complete!")