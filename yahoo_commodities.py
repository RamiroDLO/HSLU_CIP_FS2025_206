# yahoo_commodities.py
# Requires: pip install yfinance pandas
# Outputs (EU format: sep=';', decimal=','):
#   - yahoo_spot.csv     (WTI, Copper, Lithium, Aluminium, Steel; since 2011-01-01)
#   - yahoo_futures.csv  (monthly contracts Nov-2025..Nov-2027; columns prefixed by commodity)

import datetime as dt
from typing import Dict, List, Tuple
import pandas as pd
import yfinance as yf

START_DATE = "2011-01-01"

# Spot tickers (Yahoo continuous/front contracts)
SPOT = {
    "WTI_Spot": "CL=F",      # WTI Crude
    "Copper_Spot": "HG=F",   # COMEX Copper
    "Lithium_Spot": "LTH=F", # Lithium Hydroxide CIF CJK (Fastmarkets) - may be unavailable in some regions
    "Aluminium_Spot": "ALI=F",
    "Steel_Spot": "HRC=F",   # U.S. Midwest HRC (CRU) Index futures (continuous)
}

# Futures roots & exchanges to build individual-month tickers
# Format: ROOT + {MonthCode}{YY} + "." + EXCH
FUTURES_SPECS: Dict[str, Tuple[str, str]] = {
    "WTI": ("CL", "NYM"),          # e.g., CLX25.NYM
    "Copper": ("HG", "CMX"),       # e.g., HGZ25.CMX
    "Aluminium": ("ALI", "CMX"),   # e.g., ALIZ25.CMX (if unavailable, will be empty)
    "Steel": ("HRC", "CMX"),       # e.g., HRCZ25.CMX
    "Lithium": ("LTH", "CME"),     # many regions won’t have per-month LTH on Yahoo
}

RANGE_START = (2025, 11)  # Nov 2025
RANGE_END   = (2027, 11)  # Nov 2027

MONTH_CODE = {1:"F",2:"G",3:"H",4:"J",5:"K",6:"M",7:"N",8:"Q",9:"U",10:"V",11:"X",12:"Z"}

def gen_contracts(root: str, exch: str, y0: int, m0: int, y1: int, m1: int) -> List[str]:
    out = []
    cur = dt.date(y0, m0, 1)
    end = dt.date(y1, m1, 1)
    while cur <= end:
        code = MONTH_CODE[cur.month]
        yy = f"{cur.year % 100:02d}"
        out.append(f"{root}{code}{yy}.{exch}")
        # next month
        if cur.month == 12:
            cur = dt.date(cur.year + 1, 1, 1)
        else:
            cur = dt.date(cur.year, cur.month + 1, 1)
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
    spot_df.to_csv("output_files/yahoo_spot.csv", float_format="%.6f", sep=";", decimal=",")
    print(f"[OK] yahoo_spot.csv  rows={len(spot_df)} cols={spot_df.shape[1]} -> {list(spot_df.columns)}")

    # ---- Futures Nov-2025 .. Nov-2027 (multiple contracts per commodity)
    fut_frames = []
    for label, (root, exch) in FUTURES_SPECS.items():
        contracts = gen_contracts(root, exch, RANGE_START[0], RANGE_START[1], RANGE_END[0], RANGE_END[1])
        df = yf_close(contracts, START_DATE)
        if df.empty:
            print(f"[WARN] No futures data for {label} (root={root}.{exch}) — skipping.")
            continue
        df = df.rename(columns={c: f"{label}_{c}" for c in df.columns})
        fut_frames.append(df)

    if fut_frames:
        fut_all = pd.concat(fut_frames, axis=1).sort_index()
        # EU number format
        fut_all.to_csv("output_files/yahoo_futures.csv", float_format="%.6f", sep=";", decimal=",")
        print(f"[OK] yahoo_futures.csv rows={len(fut_all)} cols={fut_all.shape[1]}")
    else:
        print("[WARN] No futures retrieved for the specified range.")

if __name__ == "__main__":
    main()
