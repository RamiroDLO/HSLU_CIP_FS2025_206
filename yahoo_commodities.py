# yahoo_commodities.py
# Requires: pip install yfinance pandas
# Outputs (EU format: sep=';', decimal=','):
#   - yahoo_spot.csv     (WTI, Copper, Lithium, Aluminium, Steel, Nickel, Cobalt; since 2011-01-01)
#   - yahoo_futures.csv  (3 contracts per commodity: Mar-2026, Nov-2026, Nov-2027; from 2022 onwards)

import datetime as dt
from typing import Dict, List, Tuple
import pandas as pd
import yfinance as yf

START_DATE = "2011-01-01"
FUTURES_START_DATE = "2022-01-01"  # Limit futures data to 2022 onwards

# Spot tickers (Yahoo continuous/front contracts and proxies)
SPOT = {
    "WTI_Spot": "CL=F",      # WTI Crude
    "Copper_Spot": "HG=F",   # COMEX Copper
    "Lithium_Spot": "LIT",   # Global X Lithium & Battery Tech ETF (proxy for lithium prices)
    "Aluminium_Spot": "ALI=F",
    "Steel_Spot": "HRC=F",   # U.S. Midwest HRC (CRU) Index futures (continuous)
    "Nickel_Spot": "^SPGSIK", # S&P GSCI Nickel Index (proxy)
    "Cobalt_Spot": "NICMF",  # Nickel Industries Limited (produces nickel & cobalt; proxy)
}

# Futures roots & exchanges to build individual-month tickers
# Format: ROOT + {MonthCode}{YY} + "." + EXCH
FUTURES_SPECS: Dict[str, Tuple[str, str]] = {
    "WTI": ("CL", "NYM"),          # e.g., CLX25.NYM
    "Copper": ("HG", "CMX"),       # e.g., HGZ25.CMX
    "Aluminium": ("ALI", "CMX"),   # e.g., ALIZ25.CMX (if unavailable, will be empty)
    "Steel": ("HRC", "CMX"),       # e.g., HRCZ25.CMX
    "Lithium": ("LTH", "CME"),     # many regions won't have per-month LTH on Yahoo
}

# Specific contract months (year, month)
SPECIFIC_CONTRACTS = [
    (2026, 3),   # March 2026
    (2026, 11),  # November 2026
    (2027, 11),  # November 2027
]

MONTH_CODE = {1:"F",2:"G",3:"H",4:"J",5:"K",6:"M",7:"N",8:"Q",9:"U",10:"V",11:"X",12:"Z"}

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

    # ---- Futures for specific contracts only (March 2026, Nov 2026, Nov 2027) - LIMITED TO 2022 ONWARDS
    fut_frames = []
    for label, (root, exch) in FUTURES_SPECS.items():
        contracts = gen_contracts(root, exch, SPECIFIC_CONTRACTS)  # Pass SPECIFIC_CONTRACTS
        df = yf_close(contracts, FUTURES_START_DATE)
        if df.empty:
            print(f"[WARN] No futures data for {label} (root={root}.{exch}) — skipping.")
            continue
        df = df.rename(columns={c: f"{label}_{c}" for c in df.columns})
        fut_frames.append(df)

    if fut_frames:
        fut_all = pd.concat(fut_frames, axis=1).sort_index()
        # EU number format
        fut_all.to_csv("API_data_pull/yahoo_futures.csv", float_format="%.6f", sep=";", decimal=",")
        print(f"[OK] yahoo_futures.csv rows={len(fut_all)} cols={fut_all.shape[1]} (Mar-2026, Nov-2026, Nov-2027; data from {FUTURES_START_DATE} onwards)")
    else:
        print("[WARN] No futures retrieved for the specified range.")

if __name__ == "__main__":
    main()