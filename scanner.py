from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# The embedded scanner file is renamed to scanner_core.py in this package.
import scanner_core

RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

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
    df.to_csv(RESULTS / f"scan_{args.slot}.csv", index=False)

    if args.slot == "1000":
        old = RESULTS / "scan_0930.csv"
        if old.exists():
            a = pd.read_csv(old)
            if "Signal" in a.columns and "Signal" in df.columns:
                old_map = dict(zip(a["Symbol"], a["Signal"]))
                def confirm(row):
                    s = row.get("Signal", "")
                    prev = old_map.get(row.get("Symbol", ""), "")
                    if s == "SELECTED BUY" and prev == "SELECTED BUY": return "CONFIRMED BUY"
                    if s == "SELECTED SELL" and prev == "SELECTED SELL": return "CONFIRMED SELL"
                    if s == "SELECTED BUY": return "NEW BUY"
                    if s == "SELECTED SELL": return "NEW SELL"
                    if prev in ("SELECTED BUY","SELECTED SELL") and s not in ("SELECTED BUY","SELECTED SELL"):
                        return "REJECTED"
                    return "WATCH"
                df["Confirmation"] = df.apply(confirm, axis=1)
                df.to_csv(RESULTS / "scan_1000.csv", index=False)
