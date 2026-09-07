from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# The embedded scanner file is renamed to scanner_core.py in this package.
import scanner_core

RESULTS = ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

def run():
    symbols = scanner_core.read_symbols()
    df = scanner_core.rank_results(scanner_core.scan_all_stocks(symbols))

    numeric = [
        "Close","Wave-2 Retracement %","Wave-1 High","Wave-2 Low",
        "RSI14","EMA20","EMA50","EMA200","Volume Ratio","ATR14",
        "Fib 38.2","Fib 50","Fib 61.8","Fib 78.6","Fib 127.2",
        "Fib 161.8","Entry","Stop Loss","Target 1 (2R)",
        "Target 2 (3R)","Risk/Reward"
    ]
    for c in numeric:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").round(2)

    return df

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", choices=["0930","1000"], required=True)
    args = parser.parse_args()

    df = run()

    # For slot "1000" optionally compare with 0930 results and add Confirmation
    if args.slot == "1000":
        old = RESULTS / "scan_0930.csv"
        if old.exists():
            a = pd.read_csv(old)

            # Ensure required columns exist in both dataframes
            if {"Symbol", "Signal"}.issubset(a.columns) and {"Symbol", "Signal"}.issubset(df.columns):
                # Normalize old signals and symbols: coerce NaN -> "", strip and upper-case signals
                old_signals = a["Signal"].fillna("").astype(str).str.strip().str.upper()
                old_symbols = a["Symbol"].fillna("").astype(str).str.strip()
                old_map = dict(zip(old_symbols, old_signals))

                # Normalize new signals and symbols for safe comparison (temporary columns)
                df["_SIG_NORM"] = df["Signal"].fillna("").astype(str).str.strip().str.upper()
                df["_SYM_STR"] = df["Symbol"].fillna("").astype(str).str.strip()

                def confirm(row):
                    s = row.get("_SIG_NORM", "")  # normalized current signal
                    prev = old_map.get(row.get("_SYM_STR", ""), "")
                    if s == "SELECTED BUY" and prev == "SELECTED BUY":
                        return "CONFIRMED BUY"
                    if s == "SELECTED SELL" and prev == "SELECTED SELL":
                        return "CONFIRMED SELL"
                    if s == "SELECTED BUY":
                        return "NEW BUY"
                    if s == "SELECTED SELL":
                        return "NEW SELL"
                    if prev in ("SELECTED BUY", "SELECTED SELL") and s not in ("SELECTED BUY", "SELECTED SELL"):
                        return "REJECTED"
                    return "WATCH"

                df["Confirmation"] = df.apply(confirm, axis=1)
                # drop temp columns
                df.drop(columns=["_SIG_NORM", "_SYM_STR"], inplace=True)
            else:
                # If required columns are missing in either old or new, default to WATCH
                df["Confirmation"] = "WATCH"

    # Write the final CSV once
    df.to_csv(RESULTS / f"scan_{args.slot}.csv", index=False)
