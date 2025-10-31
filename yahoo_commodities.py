# yahoo_commodities.py
# Requires: pip install yfinance pandas
import pandas as pd
import yfinance as yf

START_DATE = "2020-01-01"

SPOT = {
    "WTI_Spot": "CL=F",
    "Copper_Spot": "HG=F",
    "Lithium_Spot": "LIT",
    "Aluminium_Spot": "ALI=F",
    "Steel_Spot": "HRC=F",
    "Nickel_Spot": "NIC.AX",
    "Cobalt_Spot": "603799.SS"
}

def fill_with_rolling_mean(df, window=7):
    """Fill NaN values with mean of previous 'window' non-empty values."""
    df_filled = df.copy()
    
    for col in df_filled.columns:
        # Create rolling mean of last 7 non-NaN values
        filled_series = df_filled[col].copy()
        
        for idx in df_filled[df_filled[col].isna()].index:
            # Get previous non-NaN values
            prev_values = df_filled.loc[:idx, col].dropna().tail(window)
            
            if len(prev_values) > 0:
                filled_series.loc[idx] = prev_values.mean()
        
        df_filled[col] = filled_series
    
    return df_filled

def main():
    # Download data
    tickers = list(SPOT.values())
    df = yf.download(tickers, start=START_DATE, progress=False)
    
    # Extract Close prices
    if isinstance(df.columns, pd.MultiIndex):
        df = df['Close'] if 'Close' in df.columns.get_level_values(0) else df['Adj Close']
    
    # Rename columns
    df.columns = [k for k, v in SPOT.items() if v in df.columns]
    
    # Fill missing values with 7-day rolling mean
    print(f"Missing values before filling: {df.isna().sum().sum()}")
    df = fill_with_rolling_mean(df, window=7)
    print(f"Missing values after filling: {df.isna().sum().sum()}")
    df = df.round(2)


    # Save as plain CSV (standard format)
    df.to_csv("API_data_pull/yahoo_spot.csv")
    print(f"✓ Saved: {len(df)} rows, {df.shape[1]} columns")
    print(f"Columns: {list(df.columns)}")

if __name__ == "__main__":
    main()