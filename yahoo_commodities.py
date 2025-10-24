# yahoo_commodities.py
# Requires: pip install yfinance pandas
# Outputs (EU format: sep=';', decimal=','):
#   - yahoo_spot.csv     (WTI, Copper, Lithium, Aluminium, Steel, Nickel, Cobalt; since 2020-01-01)

import datetime as dt
from typing import Dict, List, Tuple
import pandas as pd
import yfinance as yf

START_DATE = "2020-01-01"

# Spot tickers (Yahoo continuous/front contracts and proxies)
SPOT = {
    "WTI_Spot": "CL=F",      # WTI Crude
    "Copper_Spot": "HG=F",   # COMEX Copper
    "Lithium_Spot": "LIT",   # Global X Lithium & Battery Tech ETF (proxy for lithium prices)
    "Aluminium_Spot": "ALI=F",
    "Steel_Spot": "HRC=F",   # U.S. Midwest HRC (CRU) Index futures (continuous)
    "Nickel_Spot": "NIC.AX", # S&P GSCI Nickel Index (proxy)
    "Cobalt_Spot": "603799.SS",  # Zhejiang Huayou Cobalt (mining, refining,  manufacturing, and recycling cobalt and other materials; proxy)
}

def gen_contracts(root: str, exch: str, contracts_list: List[Tuple[int, int]]) -> List[str]:
    """Generate contract tickers for specific (year, month) tuples."""
    out = []
    for year, month in contracts_list:
        code = MONTH_CODE[month]
        yy = f"{year % 100:02d}"
        out.append(f"{root}{code}{yy}.{exch}")
    return out

def yf_close(tickers: List[str], start: str) -> pd.DataFrame:
    if not tickers: return pd.DataFrame()
    df = yf.download(tickers, start=start, progress=False, auto_adjust=False)
    if df.empty: return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        base = "Close" if "Close" in df.columns.get_level_values(0) else "Adj Close"
        out = df[base].copy()
    else:
        col = "Close" if "Close" in df.columns else "Adj Close"
        out = df[[col]].copy()
        out.columns = tickers
    return out.dropna(how="all", axis=1).sort_index()

def main():
    # ---- Spot (one column per commodity)
    spot_df = yf_close(list(SPOT.values()), START_DATE)
    rename = {v:k for k,v in SPOT.items()}
    spot_df = spot_df.rename(columns=rename)
    # keep only requested columns, in order
    cols = [c for c in SPOT.keys() if c in spot_df.columns]
    missing = [c for c in SPOT.keys() if c not in cols]
    for m in missing:
        print(f"[WARN] No spot data returned for {m} ({SPOT[m]}).")
    spot_df = spot_df[cols]
    # EU number format
    spot_df.to_csv("API_data_pull/yahoo_spot.csv", float_format="%.6f", sep=";", decimal=",")
    print(f"[OK] yahoo_spot.csv  rows={len(spot_df)} cols={spot_df.shape[1]} -> {list(spot_df.columns)}")

if __name__ == "__main__":
    main()