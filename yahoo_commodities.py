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

def main():
    # Download data
    tickers = list(SPOT.values())
    df = yf.download(tickers, start=START_DATE, progress=False)
    
    # Extract Close prices
    if isinstance(df.columns, pd.MultiIndex):
        df = df['Close'] if 'Close' in df.columns.get_level_values(0) else df['Adj Close']
    
    # Rename columns
    df.columns = [k for k, v in SPOT.items() if v in df.columns]
    
      # Add Month column in MM.YYYY format
    df.insert(0, 'Month', df.index.strftime('%m-%Y'))
    
    # Calculate monthly averages for each commodity and add as new columns
    df_monthly_avg = df.groupby('Month')[list(SPOT.keys())].transform('mean').round(2)
    
    # Rename monthly average columns
    for col in SPOT.keys():
        df[f'{col}_Monthly_Avg'] = df_monthly_avg[col]

    df = df.round(2)

    # Save as plain CSV (standard format)
    df.to_csv("API_data_pull/yahoo_spot.csv")
    print(f"✓ Saved: {len(df)} rows, {df.shape[1]} columns")
    print(f"Columns: {list(df.columns)}")

if __name__ == "__main__":
    main()