#!/usr/bin/env python3
"""
Minimal test scan script for the Streamlit app.

Usage:
  python scan.py <kind> <output_path>

This writes a tiny CSV to the requested output path so the app can load
and display a "live" scan result.
"""
import sys
from pathlib import Path
import pandas as pd


def main():
    if len(sys.argv) < 3:
        print("usage: scan.py <kind> <output_path>")
        sys.exit(1)

    kind = sys.argv[1]
    out_path = Path(sys.argv[2])
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Simple sample rows to exercise the app's filters/columns
    if kind == "scan_0930":
        rows = [
            {"Symbol": "INFY", "Signal": "SELECTED BUY"},
            {"Symbol": "TCS", "Signal": "WATCH SELL"},
        ]
    elif kind == "scan_1000":
        rows = [
            {"Symbol": "RELIANCE", "Confirmation": "CONFIRMED BUY"},
            {"Symbol": "HDFC", "Confirmation": "REJECTED"},
        ]
    else:
        # Generic sample if an unknown kind is passed
        rows = [
            {"Symbol": "ABC", "Signal": "SELECTED BUY", "Confirmation": "CONFIRMED BUY"},
        ]

    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")


if __name__ == "__main__":
    main()
