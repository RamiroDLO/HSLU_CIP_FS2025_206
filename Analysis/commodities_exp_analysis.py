import datetime as dt
from typing import Dict, List, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

df = pd.read_csv('../API_data_pull/yahoo_spot.csv', sep=';', index_col=0, decimal=',', parse_dates=True)

print(df.dtypes)
df.head()
print(df.info())


print("="*80)
print("COMMODITY PRICE DATA - EXPLORATORY ANALYSIS")
print("="*80)

print(f"\nData Range: {df.index.min()} to {df.index.max()}")
print(f"\nAmount of Dates for analysis:{len(df)}")

print(df.isnull().sum())
print(f"\nData Completeness: \n{(1 - df.isnull().sum() / len(df)) * 100}")


# Basic statistics
print(f"\n{'='*80}")
print("DESCRIPTIVE STATISTICS (Original Prices)")
print("="*80)
print(df.describe().round(2))

#percentage changes from start
print(f"\n{'='*80}")
print("TOTAL CHANGE FROM START TO END (%)")
print("="*80)

for col in df.columns:

    valid_data = df[col].dropna()
    if len(valid_data) < 2:
        print(f"{col:20s}: Insufficient data")
        continue

    start_price = valid_data.iloc[0]
    end_price = valid_data.iloc[-1]
    start_date = valid_data.index[0].strftime('%Y-%m-%d')
    end_date = valid_data.index[-1].strftime('%Y-%m-%d')
    
    pct_change = ((end_price - start_price) / start_price) * 100

    print(f"{col:20s}: {pct_change:+7.2f}%  ({start_date} → {end_date})")

#indexed values (Base 100 at start date)
df_indexed = df.copy()

print(f"\n{'='*80}")
print("INDEXING PROCESS")
print("="*80)

for col in df_indexed.columns:
    # Get first non-NaN value for this commodity
    valid_data = df[col].dropna()
    
    if len(valid_data) < 1:
        print(f"Warning: Cannot index {col} (no valid data)")
        continue
    
    start_price = valid_data.iloc[0]
    start_date = valid_data.index[0].strftime('%Y-%m-%d')
    
    if start_price != 0:
        df_indexed[col] = (df[col] / start_price) * 100
        print(f"{col:20s}: Base 100 from {start_date} (starting price: {start_price:.2f})")
    else:
        print(f"Warning: Cannot index {col} (first value is 0)")

print(f"\n{'='*80}")
print("INDEXED PRICES (Base 100 = First Available Date for Each Commodity)")
print("="*80)
print(df_indexed.head(10))
print("\n...")
print(df_indexed.tail(10))

#Viz 1: Commodities Index

plt.figure(figsize=(16, 9))
for col in df_indexed.columns:
    plt.plot(df_indexed.index, df_indexed[col], label=col, linewidth=2)

plt.axhline(y=100, color='black', linestyle='--', linewidth=1, alpha=0.5, label='Base (100)')
plt.title('Commodity Price Index (Base 100)', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Index (Base 100)', fontsize=12)
plt.legend(loc='best', fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()


# Viz 2: Calculate daily returns for each commodity (for better volatility analysis)
df_returns = df_indexed.pct_change().dropna()

fig, axes = plt.subplots(2, 4, figsize=(20, 10))
axes = axes.flatten()

colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#e67e22', '#1abc9c']

for idx, col in enumerate(df_returns.columns):
    ax = axes[idx]
    
    # Get valid returns data
    returns = df_returns[col].dropna()
    
    if len(returns) < 10:
        ax.text(0.5, 0.5, f'{col}\nInsufficient Data', 
               ha='center', va='center', fontsize=12, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        continue
    
    # Remove outliers using IQR method (especially important for WTI)
    Q1 = returns.quantile(0.25)
    Q3 = returns.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 3 * IQR  # 3x IQR for more aggressive outlier removal
    upper_bound = Q3 + 3 * IQR
    
    returns_filtered = returns[(returns >= lower_bound) & (returns <= upper_bound)]
    outliers_removed = len(returns) - len(returns_filtered)
    
    # Calculate statistics on filtered data
    mu = returns_filtered.mean()
    sigma = returns_filtered.std()
    
    # Create histogram
    n, bins, patches = ax.hist(returns_filtered, bins=50, density=True, alpha=0.6, 
                                color=colors[idx % len(colors)], edgecolor='black', linewidth=0.5)
    
    # Fit normal distribution curve
    x = np.linspace(returns_filtered.min(), returns_filtered.max(), 100)
    ax.plot(x, stats.norm.pdf(x, mu, sigma), 
           color='darkred', linewidth=2.5, label=f'Normal (μ={mu:.4f}, σ={sigma:.4f})')
    
    # Add vertical line at mean
    ax.axvline(mu, color='red', linestyle='--', linewidth=2, alpha=0.7, label=f'Mean')
    
    # Add ±1 sigma lines
    ax.axvline(mu + sigma, color='orange', linestyle=':', linewidth=1.5, alpha=0.6, label=f'±1σ')
    ax.axvline(mu - sigma, color='orange', linestyle=':', linewidth=1.5, alpha=0.6)
    
    title_text = f'{col}'
    if outliers_removed > 0:
        title_text += f'\n({outliers_removed} outliers removed)'
    
    ax.set_title(title_text, fontsize=12, fontweight='bold')
    ax.set_xlabel('Daily Returns (%)', fontsize=10)
    ax.set_ylabel('Density', fontsize=10)
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)

# Hide extra subplots if fewer than 8 commodities
for idx in range(len(df_returns.columns), len(axes)):
    fig.delaxes(axes[idx])

plt.suptitle('Commodity Volatility Distributions (Daily Returns - Outliers Removed)', 
            fontsize=16, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig('commodity_volatility_distributions.png', 
            dpi=300, bbox_inches='tight', facecolor='white')
plt.show()


# Viz 3: Summary Statistics 
df_returns = df_indexed.pct_change().dropna()

print(f"\n{'='*80}")
print("VOLATILITY SUMMARY STATISTICS (Daily Returns - With Outlier Filtering)")
print("="*80)

stats_list = []
for col in df_returns.columns:
    returns = df_returns[col].dropna()
    
    if len(returns) < 10:
        stats_list.append({
            'Commodity': col,
            'Mean (%)': np.nan,
            'Std Dev (%)': np.nan,
            'Min (%)': np.nan,
            'Max (%)': np.nan,
            'Skewness': np.nan,
            'Kurtosis': np.nan,
            'Outliers Removed': 0,
            'Valid Data Points': len(returns)
        })
        continue
    
    # Remove outliers
    Q1 = returns.quantile(0.25)
    Q3 = returns.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 3 * IQR
    upper_bound = Q3 + 3 * IQR
    returns_filtered = returns[(returns >= lower_bound) & (returns <= upper_bound)]
    
    stats_list.append({
        'Commodity': col,
        'Mean (%)': returns_filtered.mean() * 100,
        'Std Dev (%)': returns_filtered.std() * 100,
        'Min (%)': returns_filtered.min() * 100,
        'Max (%)': returns_filtered.max() * 100,
        'Skewness': returns_filtered.skew(),
        'Kurtosis': returns_filtered.kurtosis(),
        'Outliers Removed': len(returns) - len(returns_filtered),
        'Valid Data Points': len(returns_filtered)
    })

volatility_stats = pd.DataFrame(stats_list).set_index('Commodity')
print(volatility_stats.round(4))

print("\nInterpretation:")
print("- Std Dev: Higher = More volatile")
print("- Skewness: 0 = symmetric, >0 = right tail, <0 = left tail")
print("- Kurtosis: >0 = heavy tails (more extreme moves), <0 = light tails")
print("- Outliers: Removed using IQR method (Q1 - 3*IQR, Q3 + 3*IQR)")

# Viz 4: Correlation Heatmap

correlation_matrix = df.corr()
# Mask diagonal (self-correlations)
mask = np.eye(len(correlation_matrix), dtype=bool)
correlation_masked = correlation_matrix.copy()
correlation_masked[mask] = np.nan

plt.figure(figsize=(12, 10))

im = plt.imshow(correlation_masked, cmap="RdYlGn", aspect='auto', vmin=-1, vmax=1)
plt.colorbar(im, label='Correlation Coefficient')

plt.xticks(range(len(correlation_matrix.columns)), correlation_matrix.columns, 
           rotation=45, ha='right', fontsize=11)
plt.yticks(range(len(correlation_matrix.columns)), correlation_matrix.columns, fontsize=11)
plt.title('Commodity Price Correlation Matrix', fontsize=16, fontweight='bold', pad=20)

# Add correlation values (skip diagonal)
for i in range(len(correlation_matrix)):
    for j in range(len(correlation_matrix)):
        if i == j:
            # Diagonal: show light grey background with no text
            plt.gca().add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, 
                                             fill=True, color='lightgrey', alpha=0.5))
        else:
            # Non-diagonal: show correlation value
            value = correlation_matrix.iloc[i, j]
            if not np.isnan(value):
                text_color = 'white' 
                plt.text(j, i, f'{value:.2f}',
                        ha="center", va="center", color=text_color, 
                        fontsize=9, fontweight='bold')

plt.tight_layout()

# Save the figure
plt.savefig('commodity_correlation_heatmap.png', 
            dpi=300, bbox_inches='tight', facecolor='white')
print("✓ Correlation heatmap saved as: output_files/commodity_correlation_heatmap.png")

plt.show()