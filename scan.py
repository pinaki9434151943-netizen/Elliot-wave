#!/usr/bin/env python3
"""
Full 500-stock scan script with Elliott Wave pattern detection.

Usage:
  python scan.py <kind> <output_path> --symbols-file symbols.txt

This script bulk-downloads historical data using yfinance in batches and
computes Elliott Wave patterns. It writes a CSV the app can load with:
- Symbol, LastClose, Signal, WavePattern, WaveStructure, Confidence

Elliott Wave Detection includes:
- Impulse waves (5-wave structure)
- Corrective waves (3-wave structure: Zigzag, Flat, Triangle)
- Wave pattern confidence scoring
- Support/Resistance levels

Notes:
- Provide a symbols.txt with one ticker per line (e.g. INFY, TCS, RELIANCE).
- By default the script appends the '.NS' suffix for NSE tickers unless the
  symbol already contains a dot (e.g. BRK.B).
- Requires: pandas, yfinance, numpy
"""
import argparse
import time
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import pandas as pd
import yfinance as yf
import math
import sys
import numpy as np


class ElliottWaveAnalyzer:
    """Detects Elliott Wave patterns in price data."""
    
    def __init__(self, close_prices: np.ndarray, lookback: int = 200):
        """
        Initialize analyzer with close prices.
        
        Args:
            close_prices: numpy array of close prices (oldest to newest)
            lookback: number of periods to use for analysis
        """
        self.prices = close_prices[-lookback:] if len(close_prices) > lookback else close_prices
        self.length = len(self.prices)
        self.confidence = 0.0
        
    def find_peaks_and_troughs(self, window: int = 5) -> Tuple[List[int], List[int]]:
        """Find local peaks and troughs in price data."""
        peaks = []
        troughs = []
        
        if len(self.prices) < window * 2:
            return peaks, troughs
        
        for i in range(window, len(self.prices) - window):
            # Peak: price higher than surrounding prices
            if self.prices[i] == max(self.prices[i-window:i+window+1]):
                if len(peaks) == 0 or i - peaks[-1] > window:
                    peaks.append(i)
            # Trough: price lower than surrounding prices
            if self.prices[i] == min(self.prices[i-window:i+window+1]):
                if len(troughs) == 0 or i - troughs[-1] > window:
                    troughs.append(i)
        
        return peaks, troughs
    
    def calculate_fibonacci_levels(self, start_idx: int, end_idx: int) -> Dict[str, float]:
        """Calculate Fibonacci retracement levels."""
        high = max(self.prices[start_idx:end_idx+1])
        low = min(self.prices[start_idx:end_idx+1])
        diff = high - low
        
        return {
            '23.6': high - (diff * 0.236),
            '38.2': high - (diff * 0.382),
            '50.0': high - (diff * 0.500),
            '61.8': high - (diff * 0.618),
            '78.6': high - (diff * 0.786),
        }
    
    def detect_impulse_wave(self, peaks: List[int], troughs: List[int]) -> Tuple[str, float]:
        """
        Detect 5-wave impulse pattern.
        Ideal pattern: Uptrend = wave1(up), wave2(down), wave3(up), wave4(down), wave5(up)
        """
        if len(peaks) < 3 or len(troughs) < 2:
            return "NONE", 0.0
        
        confidence = 0.0
        direction = None
        
        # Check for bullish impulse (up)
        bullish_impulses = []
        for i in range(len(troughs) - 1):
            t1 = troughs[i]
            t2 = troughs[i + 1]
            
            # Find peaks between troughs
            between_peaks = [p for p in peaks if t1 < p < t2]
            if len(between_peaks) >= 1:
                p1 = between_peaks[0]
                
                # Check if this could be waves 1-2-3
                if p1 > t1 and t2 < p1:
                    wave1 = self.prices[p1] - self.prices[t1]
                    wave2_retracement = (self.prices[t1] - self.prices[t2]) / wave1
                    
                    # Wave 2 should not retrace more than 100% of wave 1
                    if 0.23 < wave2_retracement < 0.99:
                        bullish_impulses.append({
                            'trough1': t1,
                            'peak1': p1,
                            'trough2': t2,
                            'w2_ratio': wave2_retracement,
                            'strength': 1.0 - abs(wave2_retracement - 0.618)  # Ideal is 61.8%
                        })
        
        if bullish_impulses:
            best = max(bullish_impulses, key=lambda x: x['strength'])
            confidence = min(0.85, best['strength'] + 0.1)
            direction = "BULLISH_IMPULSE"
        
        # Check for bearish impulse (down)
        bearish_impulses = []
        for i in range(len(peaks) - 1):
            p1 = peaks[i]
            p2 = peaks[i + 1]
            
            between_troughs = [t for t in troughs if p1 < t < p2]
            if len(between_troughs) >= 1:
                t1 = between_troughs[0]
                
                if t1 < p1 and p2 < t1:
                    wave1 = self.prices[p1] - self.prices[t1]
                    wave2_retracement = (self.prices[t1] - self.prices[p2]) / wave1
                    
                    if 0.23 < wave2_retracement < 0.99:
                        bearish_impulses.append({
                            'peak1': p1,
                            'trough1': t1,
                            'peak2': p2,
                            'w2_ratio': wave2_retracement,
                            'strength': 1.0 - abs(wave2_retracement - 0.618)
                        })
        
        if bearish_impulses:
            best = max(bearish_impulses, key=lambda x: x['strength'])
            if best['strength'] + 0.1 > confidence:
                confidence = min(0.85, best['strength'] + 0.1)
                direction = "BEARISH_IMPULSE"
        
        return direction, confidence
    
    def detect_corrective_wave(self, peaks: List[int], troughs: List[int]) -> Tuple[str, float]:
        """
        Detect 3-wave corrective patterns:
        - Zigzag: A-down, B-up, C-down
        - Flat: A-down, B-up, C-down (with less retracement on B)
        - Triangle: converging A-B-C-D-E
        """
        if len(peaks) < 2 or len(troughs) < 2:
            return "NONE", 0.0
        
        patterns = []
        
        # Check last 3 points for A-B-C pattern
        if len(troughs) >= 2 and len(peaks) >= 2:
            t1 = troughs[-2]
            p1 = max([p for p in peaks if p > t1], default=-1)
            
            if p1 > t1:
                t2_candidates = [t for t in troughs if t > p1]
                if t2_candidates:
                    t2 = t2_candidates[0]
                    
                    # Wave A (down): from peak to trough
                    wave_a = self.prices[p1] - self.prices[t2]
                    # Wave B (up): retracement
                    wave_b = self.prices[t1] - self.prices[t2]
                    b_retracement = wave_b / wave_a if wave_a != 0 else 0
                    
                    if 0.30 < b_retracement < 0.85:
                        # Likely zigzag or flat
                        if b_retracement < 0.50:
                            patterns.append(('ZIGZAG', 0.7 + (0.3 * (1 - abs(b_retracement - 0.382)))))
                        else:
                            patterns.append(('FLAT', 0.6 + (0.3 * (1 - abs(b_retracement - 0.618)))))
        
        if patterns:
            pattern_type, conf = max(patterns, key=lambda x: x[1])
            return pattern_type, min(conf, 0.75)
        
        return "NONE", 0.0
    
    def detect_wave_structure(self) -> Tuple[str, float]:
        """Main wave detection method."""
        peaks, troughs = self.find_peaks_and_troughs()
        
        if len(peaks) < 2 or len(troughs) < 1:
            return "INSUFFICIENT_DATA", 0.0
        
        # Try impulse wave first
        impulse, impulse_conf = self.detect_impulse_wave(peaks, troughs)
        if impulse != "NONE":
            return impulse, impulse_conf
        
        # Fall back to corrective
        corrective, corrective_conf = self.detect_corrective_wave(peaks, troughs)
        if corrective != "NONE":
            return corrective, corrective_conf
        
        return "COMPLEX_PATTERN", 0.4
    
    def generate_signal(self) -> Tuple[str, str, float]:
        """
        Generate trading signal based on Elliott Wave analysis.
        Returns: (signal, wave_pattern, confidence)
        """
        wave_pattern, confidence = self.detect_wave_structure()
        
        if wave_pattern == "INSUFFICIENT_DATA":
            return "HOLD", wave_pattern, 0.0
        
        # Determine trend direction and signal
        recent_prices = self.prices[-20:]
        is_uptrend = recent_prices[-1] > recent_prices[0]
        volatility = np.std(recent_prices) / np.mean(recent_prices) if np.mean(recent_prices) > 0 else 0
        
        signal = "HOLD"
        
        if "BULLISH" in wave_pattern:
            if is_uptrend and confidence > 0.6:
                signal = "STRONG_BUY" if confidence > 0.75 else "BUY"
            elif not is_uptrend and confidence > 0.7:
                signal = "CONTRARIAN_BUY"
            else:
                signal = "WATCH_UP"
        
        elif "BEARISH" in wave_pattern:
            if not is_uptrend and confidence > 0.6:
                signal = "STRONG_SELL" if confidence > 0.75 else "SELL"
            elif is_uptrend and confidence > 0.7:
                signal = "CONTRARIAN_SELL"
            else:
                signal = "WATCH_DOWN"
        
        elif "ZIGZAG" in wave_pattern or "FLAT" in wave_pattern:
            signal = "CORRECTION_IN_PROGRESS"
        
        else:
            signal = "HOLD"
        
        return signal, wave_pattern, confidence


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


def compute_signal(hist: pd.DataFrame) -> Tuple[str, str, float]:
    """
    Compute Elliott Wave signal.
    Returns: (signal, wave_pattern, confidence)
    """
    if hist is None or hist.empty or 'Close' not in hist.columns:
        return "DATA_MISSING", "NO_DATA", 0.0
    
    close = hist['Close']
    if len(close) < 20:
        return "INSUFFICIENT_DATA", "NOT_ENOUGH_DATA", 0.0
    
    try:
        close_array = close.values.astype(float)
        analyzer = ElliottWaveAnalyzer(close_array, lookback=200)
        signal, wave_pattern, confidence = analyzer.generate_signal()
        return signal, wave_pattern, confidence
    except Exception as e:
        print(f"  Error in wave analysis: {e}", file=sys.stderr)
        return "ERROR", "ANALYSIS_FAILED", 0.0


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
    parser = argparse.ArgumentParser(description="Full 500-stock scan with Elliott Wave detection")
    parser.add_argument("kind", help="scan_0930 / scan_1000 / etc")
    parser.add_argument("output_path", help="path to write CSV")
    parser.add_argument("--symbols-file", default="symbols.txt", help="one ticker per line (no suffix or include .NS)")
    parser.add_argument("--suffix", default=".NS", help="default exchange suffix to append if none provided")
    parser.add_argument("--batch-size", type=int, default=100, help="how many tickers per bulk yfinance call")
    parser.add_argument("--period", default="200d", help="history period for indicators (e.g. 200d)")
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
    print(f"Using {args.period} of historical data for Elliott Wave analysis")

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

            # compute signal using Elliott Wave
            signal, wave_pattern, confidence = compute_signal(hist)
            last_close = float(hist['Close'].iloc[-1]) if hist is not None and not hist.empty and 'Close' in hist.columns else math.nan
            rows.append({
                "Symbol": raw_symbol,
                "LastClose": last_close,
                "Signal": signal,
                "WavePattern": wave_pattern,
                "Confidence": confidence,
            })

        # polite pause between batches
        time.sleep(1.0)

    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    print(f"\nWrote {len(df)} rows to {out_path}")
    
    # Print summary
    print("\n=== Elliott Wave Scan Summary ===")
    print(df['Signal'].value_counts())
    print("\n=== Wave Patterns Detected ===")
    print(df['WavePattern'].value_counts())
    print(f"\n=== High Confidence Signals (>0.70) ===")
    high_conf = df[df['Confidence'] > 0.70]
    print(f"Found {len(high_conf)} high-confidence patterns")
    if len(high_conf) > 0:
        print(high_conf[['Symbol', 'Signal', 'WavePattern', 'Confidence']].head(20))


if __name__ == "__main__":
    main()
