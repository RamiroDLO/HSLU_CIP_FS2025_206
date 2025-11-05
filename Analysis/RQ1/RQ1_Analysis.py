"""
RQ1: Correlation between Swiss used-car prices and commodity indices
Columns present (per screenshot): brand, model, car_model, price_chf, mileage, production_date,
Month, WTI/Copper/Lithium/Aluminium/Steel/Nickel/Cobalt _Spot_Monthly_Avg (+ _indexed), Composite_Index
"""

import os, numpy as np, pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

print("Current directory:", os.getcwd())
PATH_MERGED = "Data/Final Data/Final_Merged_Data_RQ3.csv"
OUTDIR = "Analysis/RQ1"
os.makedirs(OUTDIR, exist_ok=True)

print("="*80)
print("RQ1: COMMODITY PRICES vs USED CAR PRICES CORRELATION ANALYSIS")
print("="*80)

# 1) LOAD
print("\n[1] Loading merged dataset...")
df = pd.read_csv(PATH_MERGED)
df.info(1)
print(f"   Rows: {len(df):,}")
print(f"   Columns: {list(df.columns)}")

# 2) COMMODITY COLUMNS 
commodity_cols = [
    'WTI_Spot_Monthly_Avg','Steel_Spot_Monthly_Avg','Aluminium_Spot_Monthly_Avg',
    'Copper_Spot_Monthly_Avg','Cobalt_Spot_Monthly_Avg','Nickel_Spot_Monthly_Avg',
    'Lithium_Spot_Monthly_Avg'
]
commodity_cols = [c for c in commodity_cols if c in df.columns]

weights = {  # only used if we must rebuild composite
    'WTI_Spot_Monthly_Avg': 0.30,
    'Steel_Spot_Monthly_Avg': 0.15,
    'Aluminium_Spot_Monthly_Avg': 0.25,
    'Copper_Spot_Monthly_Avg': 0.05,
    'Cobalt_Spot_Monthly_Avg': 0.05,
    'Nickel_Spot_Monthly_Avg': 0.05,
    'Lithium_Spot_Monthly_Avg': 0.15,
}



# 3) MONTHLY AGG (one row per Month)
print("\n[3] Aggregating to monthly level...")
agg_map = {"price_chf": ["median","mean","count"], "mileage": "mean"}
use_cols = ['Month','price_chf','mileage','Composite_Index'] + commodity_cols
df_small = df[use_cols].copy()

monthly = (
    df_small
    .groupby("Month", as_index=False)
    .agg({**agg_map, "Composite_Index": "mean", **{c: "mean" for c in commodity_cols}})
)

# flatten columns
monthly.columns = ['Month','median_price','mean_price','car_count','avg_mileage',
                   'Composite_Index'] + commodity_cols
print(f"   Aggregated to {len(monthly)} months | total cars = {int(monthly['car_count'].sum()):,}")

# parse Month for plotting (accept 06.2024 or 06-2024)
def _to_month(s):
    for fmt in ("%m.%Y","%m-%Y","%Y-%m","%Y.%m"):
        try: return pd.to_datetime(s, format=fmt)
        except: pass
    return pd.NaT
monthly["Month_Date"] = monthly["Month"].apply(_to_month)

# 4) COMPOSITE INDEX (use existing; rebuild only if missing)
print("\n[2] Checking Composite_Index...")
if 'Composite_Index' not in df.columns:
    print("   Composite_Index missing → rebuilding (base=first non-null of each series).")
    # index each monthly series to base=100 and weight
    comp = 0.0
    for col in commodity_cols:
        s = df[col]
        base = s.dropna().iloc[0]
        idx = (s / base) * 100.0
        df[f"{col}_indexed"] = idx
        comp = comp + idx * weights.get(col, 0.0)
    df['Composite_Index'] = comp
else:
    print("   Composite_Index present.")



# 5) CORRELATIONS (drop NA pairs)
print("\n[4] Computing correlations...")
def corr_pair(x, y):
    d = monthly[[x, y]].dropna()
    if len(d) < 3: return np.nan, np.nan, len(d)
    r_p = stats.pearsonr(d[x], d[y])
    r_s = stats.spearmanr(d[x], d[y])
    return (r_p[0], r_p[1], len(d)), (r_s.correlation, r_s.pvalue, len(d))

(pearson_c, spearman_c) = corr_pair('median_price','Composite_Index')
if isinstance(pearson_c, tuple):
    print(f"   Composite -> Pearson r={pearson_c[0]:+.4f} (p={pearson_c[1]:.4f}) | n={pearson_c[2]}")
    print(f"               Spearman ρ={spearman_c[0]:+.4f} (p={spearman_c[1]:.4f}) | n={spearman_c[2]}")
else:
    print("   Not enough data for Composite correlation.")

print("\n   Individual commodities:")
indiv = {}
for col in commodity_cols:
    (pc, sc) = corr_pair('median_price', col)
    if isinstance(pc, tuple):
        indiv[col] = {"pearson_r": pc[0], "pearson_p": pc[1], "spearman_r": sc[0], "spearman_p": sc[1], "n": pc[2]}
        print(f"   {col.replace('_Spot_Monthly_Avg',''):<12} -> r={pc[0]:+.4f} (p={pc[1]:.4f}),  ρ={sc[0]:+.4f} (p={sc[1]:.4f}), n={pc[2]}")
    else:
        print(f"   {col}: insufficient data")

# 6) PLOTS
print("\n[5] Creating visualizations...")

# --- Filter from 2020-01-01 and sort
start_date = pd.Timestamp("2020-01-01")
monthly_filtered = (
    monthly.loc[monthly["Month_Date"] >= start_date]
           .sort_values("Month_Date")
           .copy()
)

# --- INDEX PRICES TO BASE 100 AT 2020-01 ---
base_jan_2020 = monthly_filtered[monthly_filtered["Month_Date"] == start_date]

if len(base_jan_2020) > 0:
    base_composite = base_jan_2020["Composite_Index"].iloc[0]
    monthly_filtered["Composite_Index_Indexed"] = (monthly_filtered["Composite_Index"] / base_composite) * 100
else:
    # If no data at exactly 2020-01, use first available
    base_composite = monthly_filtered["Composite_Index"].iloc[0]
    monthly_filtered["Composite_Index_Indexed"] = (monthly_filtered["Composite_Index"] / base_composite) * 100
    print(f"   ⚠ No data at 2020-01-01, using first month: {monthly_filtered['Month_Date'].iloc[0]}")

# --- Time series (dual axis)

if 'power_mode' in df.columns:
    # Categorize: EV vs ICE (Gasoline/Diesel)
    df['vehicle_type'] = df['power_mode'].apply(
        lambda x: 'EV' if str(x).lower() in ['elektro', 'electric', 'ev'] else 'ICE'
    )
    
    # --- Monthly aggregation BY vehicle_type
    print("   Aggregating by Month AND vehicle_type...")
    agg_map = {"price_chf": ["median","mean","count"], "mileage": "mean"}
    use_cols = ['Month','price_chf','mileage','Composite_Index','vehicle_type'] + commodity_cols
    df_small = df[use_cols].copy()
    
    monthly_by_type = (
        df_small
        .groupby(["Month", "vehicle_type"], as_index=False)
        .agg({**agg_map, "Composite_Index": "mean", **{c: "mean" for c in commodity_cols}})
    )
    
    # Flatten columns
    monthly_by_type.columns = ['Month','vehicle_type','median_price','mean_price','car_count',
                                'avg_mileage','Composite_Index'] + commodity_cols
    
    # Parse Month
    monthly_by_type["Month_Date"] = monthly_by_type["Month"].apply(_to_month)
    
    # Filter from 2020
    monthly_by_type_filtered = monthly_by_type[monthly_by_type["Month_Date"] >= pd.Timestamp("2020-01-01")].copy()
    
    # --- INDEX PRICES TO BASE 100 AT 2020-01 FOR EACH TYPE ---
    for vtype in ['ICE', 'EV']:
        type_data = monthly_by_type_filtered[monthly_by_type_filtered['vehicle_type'] == vtype].sort_values('Month_Date')
        if len(type_data) > 0:
            base_price = type_data.iloc[0]['median_price']
            monthly_by_type_filtered.loc[monthly_by_type_filtered['vehicle_type'] == vtype, 'median_price_indexed'] = (
                monthly_by_type_filtered.loc[monthly_by_type_filtered['vehicle_type'] == vtype, 'median_price'] / base_price
            ) * 100
    
    # Separate EV and ICE
    ice_data = monthly_by_type_filtered[monthly_by_type_filtered['vehicle_type'] == 'ICE'].sort_values('Month_Date')
    ev_data = monthly_by_type_filtered[monthly_by_type_filtered['vehicle_type'] == 'EV'].sort_values('Month_Date')
    
    print(f"   ICE: {len(ice_data)} months, {ice_data['car_count'].sum():.0f} cars")
    print(f"   EV:  {len(ev_data)} months, {ev_data['car_count'].sum():.0f} cars")
    
    
    # --- Time series plot with TWO price lines (INDEXED)
    fig, ax1 = plt.subplots(figsize=(16, 7))
    
    # Plot ICE prices indexed (blue)
    if len(ice_data) > 0:
        ax1.plot(ice_data["Month_Date"], ice_data["median_price"],
                 linewidth=2.5, marker="o", ms=4, label="ICE Median Price ", 
                 color='steelblue', alpha=0.8)
    
    # Plot EV prices indexed (green)
    if len(ev_data) > 0:
        ax1.plot(ev_data["Month_Date"], ev_data["median_price"],
                 linewidth=2.5, marker="^", ms=4, label="EV Median Price", 
                 color='green', alpha=0.8)
    
    ax1.set_ylabel("Median Price (CHF)", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Year", fontsize=12)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Second axis for Composite Index (also indexed)
    ax2 = ax1.twinx()
    ax2.plot(monthly_filtered["Month_Date"], monthly_filtered["Composite_Index_Indexed"],
             linestyle="--", linewidth=2.5, marker="s", ms=4, 
             label="Composite Index (Base 100 = 2020-01)", color="darkred", alpha=0.7)
    ax2.set_ylabel("Composite Commodity Index (Base 100 = 2020-01)", fontsize=12, fontweight='bold', color='darkred')
    ax2.tick_params(axis='y', labelcolor='darkred')
    ax2.legend(loc='upper right', fontsize=10)
    
    # Force x-axis limits
    xmin = pd.Timestamp("2020-01-01")
    xmax = monthly_by_type_filtered["Month_Date"].max()
    ax1.set_xlim(left=xmin, right=xmax)
    
    plt.title("Used Car Median Prices (ICE vs EV) vs Composite Commodity Index (Base 100 = 2020-01)", 
              fontsize=14, fontweight='bold', pad=20)
    fig.tight_layout()
    plt.savefig(f"{OUTDIR}/RQ1_timeseries.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("   ✓ Saved: RQ1_timeseries.png")

# Scatter
fig, ax = plt.subplots(figsize=(10,7))
ax.scatter(monthly['Composite_Index'], monthly['median_price'], alpha=.7, edgecolors='k')
if monthly['Composite_Index'].notna().sum() >= 3:
    z = np.polyfit(monthly['Composite_Index'].dropna(), monthly['median_price'][monthly['Composite_Index'].notna()], 1)
    p = np.poly1d(z); xs = np.linspace(monthly['Composite_Index'].min(), monthly['Composite_Index'].max(), 200)
    ax.plot(xs, p(xs), 'r--', lw=2)
ax.set_xlabel('Composite Commodity Index (Base 100)'); ax.set_ylabel('Median Car Price (CHF)')
ax.grid(True, alpha=.3)
plt.title('Correlation: Car Prices vs Composite Index')
fig.tight_layout(); plt.savefig(f"{OUTDIR}/RQ1_scatter.png", dpi=300); plt.close()
print("   ✓ Saved: RQ1_scatter.png")

# 8) SUMMARY
print("\n" + "="*80)
print("RQ1 ANALYSIS COMPLETE")
print("="*80)
print(f"   • Sample: {len(monthly)} months, {int(monthly['car_count'].sum()):,} total cars")
if isinstance(pearson_c, tuple):
    print(f"   • Composite Index Correlation: r={pearson_c[0]:+.3f}, ρ={spearman_c[0]:+.3f}")
if indiv:
    strongest = max(indiv.items(), key=lambda kv: abs(kv[1]["pearson_r"]))
    print(f"   • Strongest commodity: {strongest[0].replace('_Spot_Monthly_Avg','')} (r={strongest[1]['pearson_r']:+.3f})")
print(f"Outputs → {OUTDIR}/")


df[['Month','Composite_Index']]