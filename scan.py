#!/usr/bin/env python3
"""
Full 500-stock scan script for the Streamlit app.

Usage:
  python scan.py <kind> <output_path> --symbols-file symbols.txt

This script bulk-downloads historical data using yfinance in batches and
computes simple SMA-based example signals. It writes a CSV the app can
load. Replace the example signal logic with your Elliot-wave rules.

Notes:
- Provide a symbols.txt with one ticker per line (e.g. INFY, TCS, RELIANCE).
- By default the script appends the '.NS' suffix for NSE tickers unless the
  symbol already contains a dot (e.g. BRK.B).
- Requires: pandas, yfinance
"""
import argparse
import time
from pathlib import Path
from typing import List
import pandas as pd
import yfinance as yf
import math
import sys


def read_symbols(path: Path) -> List[str]:
    if not path.exists():
        return []
    txt = path.read_text().splitlines()
    syms = [s.strip().upper() for s in txt if s.strip() and not s.strip().startswith("#")]
    return syms


def normalize_symbol(s: str, default_suffix: str) -> str:
    # If user included an exchange suffix like .NS or .BO, keep it.
    return s if ('.' in s) else s + default_suffix


def chunked(iterable, n):
    for i in range(0, len(iterable), n):
        yield iterable[i:i + n]


def compute_signal(hist: pd.DataFrame) -> str:
    # hist is a DataFrame with 'Close' column (oldest -> newest)
    if hist is None or hist.empty or 'Close' not in hist.columns:
        return "DATA_MISSING"
    close = hist['Close']
    if len(close) < 5:
        return "INSUFFICIENT_DATA"
    sma20 = close.rolling(window=20, min_periods=5).mean().iloc[-1]
    sma50 = close.rolling(window=50, min_periods=10).mean().iloc[-1]
    last = close.iloc[-1]
    # Example rules (replace with your actual strategy)
    if pd.notna(sma20) and pd.notna(sma50):
        if sma20 > sma50 and last > sma20:
            return "CONFIRMED BUY"
        if sma20 > sma50:
            return "WATCH BUY"
        if sma20 < sma50 and last < sma20:
            return "CONFIRMED SELL"
        if sma20 < sma50:
            return "WATCH SELL"
    # fallback simple rule
    return "NEUTRAL" if last >= close.mean() else "WEAK"


def fetch_batch(tickers: List[str], period: str = "90d", interval: str = "1d"):
    # yfinance.download returns different shapes depending on number of tickers.
    df = yf.download(
        tickers=tickers,
        period=period,
        interval=interval,
        group_by='ticker',
        threads=True,
        progress=False,
    )
    return df


def main():
    parser = argparse.ArgumentParser(description="Full 500-stock scan")
    parser.add_argument("kind", help="scan_0930 / scan_1000 / etc")
    parser.add_argument("output_path", help="path to write CSV")
    parser.add_argument("--symbols-file", default="symbols.txt", help="one ticker per line (no suffix or include .NS)")
    parser.add_argument("--suffix", default=".NS", help="default exchange suffix to append if none provided")
    parser.add_argument("--batch-size", type=int, default=100, help="how many tickers per bulk yfinance call")
    parser.add_argument("--period", default="90d", help="history period for indicators (e.g. 90d)")
    args = parser.parse_args()

    out_path = Path(args.output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    symbols_path = Path(args.symbols_file)
    raw_syms = read_symbols(symbols_path)

    # Fallback: if no symbols file provided or found, use a tiny built-in sample
    if not raw_syms:
        print(f"Symbols file {symbols_path} not found or empty. Using a small built-in sample.", file=sys.stderr)
        raw_syms = [
            "INFY",
            "TCS",
            "RELIANCE",
            "HDFC",
        ]

    tickers = [normalize_symbol(s, args.suffix) for s in raw_syms]
    print(f"Scanning {len(tickers)} tickers in batches of {args.batch_size}...")

    rows = []
    for batch_idx, batch in enumerate(chunked(tickers, args.batch_size), start=1):
        print(f"[{batch_idx}] fetching {len(batch)} tickers...")
        # retry logic
        max_attempts = 3
        backoff = 2
        data = None
        for attempt in range(1, max_attempts + 1):
            try:
                data = fetch_batch(batch, period=args.period)
                break
            except Exception as e:
                print(f"  fetch failed attempt {attempt}: {e}", file=sys.stderr)
                if attempt < max_attempts:
                    time.sleep(backoff * attempt)
                else:
                    print("  giving up on this batch, marking as failed.", file=sys.stderr)

        for raw_symbol in batch:
            # when group_by='ticker', data is a dict-like DataFrame with top-level columns per ticker
            hist = None
            try:
                if isinstance(data.columns, pd.MultiIndex):
                    # multi-ticker: data['TICKER'] yields a sub-DataFrame
                    sym = raw_symbol
                    if sym in data.columns.levels[0]:
                        hist = data[sym].dropna(how='all')
                    else:
                        # yfinance sometimes returns tickers without the suffix removed, try fallback
                        possible = [c for c in data.columns.levels[0] if c.upper() == sym.upper()]
                        if possible:
                            hist = data[possible[0]].dropna(how='all')
                else:
                    # single-ticker return
                    hist = data
            except Exception:
                hist = None

            # compute signal
            signal = compute_signal(hist) if hist is not None and not hist.empty else "DATA_MISSING"
            last_close = float(hist['Close'].iloc[-1]) if hist is not None and not hist.empty and 'Close' in hist.columns else math.nan
            rows.append({
                "Symbol": raw_symbol,
                "LastClose": last_close,
                "Signal": signal,
            })

        # polite pause between batches
        time.sleep(1.0)

    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")


if __name__ == "__main__":
    main()
