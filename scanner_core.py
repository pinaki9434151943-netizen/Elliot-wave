"""
NIFTY 500 ELLIOTT WAVE SCANNER
Rule-based Elliott Wave / technical scanner for Nifty 500.

Input:  None — the 500 Nifty symbols are embedded in this file.
Output: Nifty500_Scanner_Result.xlsx

Install:
pip install pandas numpy openpyxl yfinance pytz beautifulsoup4 requests multitasking frozendict peewee curl_cffi websockets

Run:
python nifty500_scanner.py
"""

import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf

EMBEDDED_SYMBOLS = ['RBLBANK', 'BRIGADE', 'CAPLIPOINT', 'SOLARINDS', 'LICHSGFIN', 'CGCL', 'JMFINANCIL', 'REDINGTON', 'WELCORP', 'PTCIL', 'BEML', 'USHAMART', 'IDFCFIRSTB', 'DLF', 'URBANCO', 'NAVINFLUOR', 'ANTHEM', 'POLICYBZR', 'TBOTEK', 'ASAHIINDIA', 'ANANDRATHI', 'SAGILITY', 'KOTAKBANK', 'OIL', 'ETERNAL', 'LENSKART', 'WELSPUNLIV', 'SWIGGY', 'MAHABANK', 'KIRLOSENG', 'INDUSINDBK', 'TEJASNET', 'PHOENIXLTD', 'FEDERALBNK', 'NAM-INDIA', 'KPRMILL', 'PINELABS', 'RELIANCE', 'BEL', 'NUVAMA', 'SUNDARMFIN', 'SCI', 'SUNPHARMA', '360ONE', 'BALKRISIND', 'CPPLUS', 'NCC', 'ZYDUSLIFE', 'MANAPPURAM', 'COCHINSHIP', 'CONCORDBIO', 'HFCL', 'BLUEJET', 'AUBANK', 'NSLNISP', 'WHIRLPOOL', 'APOLLOTYRE', 'MINDACORP', 'DALBHARAT', 'LTFOODS', 'FIRSTCRY', 'AFFLE', 'DEEPAKFERT', 'HUDCO', 'GODREJCP', 'AIAENG', 'UCOBANK', 'UBL', 'JKCEMENT', 'NTPCGREEN', 'OLECTRA', 'SOBHA', 'SJVN', 'AAVAS', 'CHAMBLFERT', 'CEATLTD', 'BHARATFORG', 'CENTRALBK', 'JSWCEMENT', 'HINDUNILVR', 'DABUR', 'ITC', 'BIKAJI', 'MARUTI', 'MARICO', 'BANDHANBNK', 'RVNL', 'TATAPOWER', 'THERMAX', 'EMAMILTD', 'HDFCBANK', 'HONAUT', 'KEC', 'CANBK', 'BAYERCROP', 'SWANCORP', 'COLPAL', 'M&M', 'WAAREEENER', 'IGIL', 'JSWENERGY', 'NTPC', 'FORCEMOT', 'JPPOWER', 'ERIS', 'LEMONTREE', 'PFC', 'ASIANPAINT', 'IRFC', 'LATENTVIEW', 'GMRAIRPORT', 'IRCON', 'SONATSOFTW', 'SCHAEFFLER', 'AADHARHFC', 'SBIN', 'CIEINDIA', 'CIPLA', 'SBILIFE', 'TATACONSUM', 'COROMANDEL', 'JIOFIN', 'VOLTAS', 'IEX', 'LINDEINDIA', 'NIVABUPA', 'PATANJALI', 'SHREECEM', 'ACC', 'VBL', 'BELRISE', 'RITES', 'ALKEM', 'POLYCAB', 'SCHNEIDER', 'BRITANNIA', 'CESC', 'KPITTECH', 'MSUMI', 'RECLTD', 'ENRIN', 'ABLBL', 'INTELLECT', 'TRENT', 'LLOYDSME', 'BANKBARODA', 'GODFRYPHLP', 'GRSE', 'KIMS', 'ICICIGI', 'CHOLAHLDNG', 'HAVELLS', 'ITCHOTELS', 'JWL', 'TMPV', 'TRIDENT', 'UTIAMC', 'POWERINDIA', '3MINDIA', 'ASTERDM', 'ABFRL', 'STARHEALTH', 'BIOCON', 'IRCTC', 'ATGL', 'BERGEPAINT', 'PIIND', 'TATAELXSI', 'TIMKEN', 'LUPIN', 'GILLETTE', 'HINDPETRO', 'TATAINVEST', 'NATCOPHARM', 'ADANIENSOL', 'ADANIENT', 'INDIACEM', 'CUMMINSIND', 'TATACHEM', 'DMART', 'IKS', 'ZEEL', 'AMBUJACEM', 'INDIAMART', 'JKTYRE', 'NESTLEIND', 'CROMPTON', 'BHARTIHEXA', 'SUNTV', 'BLS', 'ZFCVINDIA', 'BDL', 'GODREJIND', 'HSCL', 'ABBOTINDIA', 'ITI', 'ARE&M', 'MGL', 'RAILTEL', 'CARBORUNIV', 'SARDAEN', 'DRREDDY', 'RHIM', 'TRAVELFOOD', 'TEGA', 'BATAINDIA', 'TENNIND', 'JSL', 'INDIANB', 'UNIONBANK', 'PNB', 'KAJARIACER', 'CASTROLIND', 'ELECON', 'ANANTRAJ', 'HEXT', 'TORNTPOWER', 'GRANULES', 'IRB', 'INOXWIND', 'IFCI', 'GICRE', 'BAJAJHLDNG', 'GODREJPROP', 'NUVOCO', 'AEGISVOPAK', 'OBEROIRLTY', 'APLAPOLLO', 'SAILIFE', 'IOB', 'JYOTICNC', 'IIFL', 'GRASIM', 'PRESTIGE', 'NIACL', 'NHPC', 'SHRIRAMFIN', 'J&KBANK', 'KARURVYSYA', 'COALINDIA', 'INDIGO', 'RRKABEL', 'WOCKPHARMA', 'SIGNATURE', 'KEI', 'ATUL', 'GESHIP', 'ADANIPORTS', 'INDHOTEL', 'ZENSARTECH', 'BANKINDIA', 'EIHOTEL', 'MRF', 'OLAELEC', 'LODHA', 'CLEAN', 'GRAVITA', 'BSE', 'APARINDS', 'BAJAJ-AUTO', 'CANFINHOME', 'JINDALSTEL', 'ENGINERSIN', 'APTUS', 'BAJFINANCE', 'MEESHO', 'RAINBOW', 'SUPREMEIND', 'BALRAMCHIN', 'PVRINOX', 'UNITDSPR', 'POWERGRID', 'NETWEB', 'DIVISLAB', 'YESBANK', 'SBICARD', 'CCL', 'HYUNDAI', 'SHYAMMETL', 'ICICIBANK', 'CGPOWER', 'CUB', 'GALLANTT', 'ECLERX', 'MEDANTA', 'JSWINFRA', 'PAGEIND', 'ULTRACEMCO', 'ABREL', 'PERSISTENT', 'EICHERMOT', 'AUROPHARMA', 'OFSS', 'TORNTPHARM', 'CAMS', 'ABSLAMC', 'BAJAJHFL', 'HEG', 'HDBFS', 'CEMPRO', 'GABRIEL', 'HOMEFIRST', 'M&MFIN', 'PIRAMALFIN', 'SIEMENS', 'BLUESTARCO', 'GLENMARK', 'JSWDULUX', 'SBFC', 'ACE', 'SRF', 'ANGELONE', 'CARTRADE', 'MPHASIS', 'FIVESTAR', 'AFCONS', 'BPCL', 'COFORGE', 'UNOMINDA', 'MCX', 'SAREGAMA', 'TATACOMM', 'TMCV', 'ATHERENERG', 'DELHIVERY', 'PETRONET', 'ADANIPOWER', 'AEGISLOG', 'DCMSHRIRAM', 'HDFCAMC', 'INDUSTOWER', 'ONESOURCE', 'ABB', 'CREDITACC', 'EIDPARRY', 'GRAPHITE', 'PWL', 'CHOLAFIN', 'LALPATHLAB', 'GAIL', 'THELEELA', 'TATASTEEL', 'UPL', 'IREDA', 'KAYNES', 'TITAGARH', 'ACUTAAS', 'FINCABLES', 'JSWSTEEL', 'DOMS', 'HCLTECH', 'ICICIAMC', 'MRPL', 'PFOCUS', 'SONACOMS', 'SUZLON', 'WIPRO', 'ESCORTS', 'RADICO', 'DIXON', 'HEROMOTOCO', 'CDSL', 'JAINREC', 'TVSMOTOR', 'BHEL', 'CHENNPETRO', 'SAMMAANCAP', 'KALYANKJIL', 'LT', 'EMCURE', 'NMDC', 'SAIL', 'ADANIGREEN', 'ENDURANCE', 'INFY', 'JBMA', 'SUMICHEM', 'TCS', 'CRAFTSMAN', 'PIDILITIND', 'TITAN', 'AXISBANK', 'LTF', 'TECHM', 'CRISIL', 'NAVA', 'TATACAP', 'ELGIEQUIP', 'GVT&D', 'JINDALSAW', 'NBCC', 'KPIL', 'MAPMYINDIA', 'PARADEEP', 'PPLPHARMA', 'ABCAPITAL', 'NYKAA', 'HBLENGINE', 'IDEA', 'APOLLOHOSP', 'DATAPATTNS', 'IOC', 'ASHOKLEY', 'PCBL', 'PGEL', 'BSOFT', 'AJANTPHARM', 'HINDZINC', 'MUTHOOTFIN', 'RPOWER', 'ZYDUSWELL', 'AIIL', 'GMDCLTD', 'HDFCLIFE', 'BAJAJFINSV', 'LTM', 'NLCINDIA', 'POLYMED', 'CHOICEIN', 'SYRMA', 'SYNGENE', 'BHARTIARTL', 'PNBHOUSING', 'PREMIERENE', 'FORTIS', 'JUBLINGREA', 'NATIONALUM', 'NEULANDLAB', 'DEEPAKNTR', 'GPIL', 'KFINTECH', 'MOTHERSON', 'TECHNOE', 'BOSCHLTD', 'EXIDEIND', 'INDGN', 'NEWGEN', 'TIINDIA', 'IDBI', 'VEDL', 'FSL', 'HAL', 'ACMESOLAR', 'LTTS', 'LAURUSLABS', 'ONGC', 'RKFORGE', 'COHANCE', 'FLUOROCHEM', 'MAZDOCK', 'POONAWALLA', 'ZENTEC', 'IPCALAB', 'NH', 'TRITURBINE', 'ASTRAL', 'ICICIPRULI', 'AARTIIND', 'GROWW', 'TATATECH', 'TARIL', 'VIJAYA', 'ABDL', 'MFSL', 'MOTILALOFS', 'PAYTM', 'BLUEDART', 'LICI', 'HINDALCO', 'EMMVEE', 'MAXHEALTH', 'GODIGIT', 'CONCOR', 'JUBLPHARMA', 'HINDCOPPER', 'VMM', 'GLAXO', 'HONASA', 'IGL', 'MMTC', 'AWL', 'AMBER', 'MANKIND', 'ANURAS', 'TTML', 'NAUKRI', 'CYIENT', 'LGEINDIA', 'SPLPETRO', 'VTL', 'GLAND', 'RAMCOCEM', 'PFIZER', 'CANHLIFE', 'DEVYANI', 'CHALET', 'JUBLFOOD', 'SAPPHIRE', 'FACT', 'BBTC']
OUTPUT_FILE = "Nifty500_Scanner_Result.xlsx"
HISTORY_PERIOD = "2y"
MAX_WORKERS = 8
PIVOT_LEFT = 3
PIVOT_RIGHT = 3
MIN_HISTORY = 220
VOLUME_MULTIPLIER = 1.50
RSI_BUY_MIN, RSI_BUY_MAX = 55, 75
RSI_SELL_MIN, RSI_SELL_MAX = 25, 45
MAX_WAVE2_RETRACEMENT = 0.786


def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calculate_atr(df, period=14):
    previous_close = df["Close"].shift(1)
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - previous_close).abs(),
        (df["Low"] - previous_close).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def find_pivots(df, left=3, right=3):
    highs = df["High"].to_numpy()
    lows = df["Low"].to_numpy()
    ph = np.zeros(len(df), dtype=bool)
    pl = np.zeros(len(df), dtype=bool)
    for i in range(left, len(df) - right):
        if highs[i] >= np.max(highs[i-left:i+right+1]):
            ph[i] = True
        if lows[i] <= np.min(lows[i-left:i+right+1]):
            pl[i] = True
    return ph, pl


def alternating_swings(df, pivot_high, pivot_low):
    swings = []
    for i in range(len(df)):
        if pivot_high[i]:
            swings.append((i, "H", float(df["High"].iloc[i])))
        if pivot_low[i]:
            swings.append((i, "L", float(df["Low"].iloc[i])))
    swings.sort(key=lambda x: x[0])
    out = []
    for swing in swings:
        if not out:
            out.append(swing)
            continue
        prev = out[-1]
        if swing[1] != prev[1]:
            out.append(swing)
        elif (swing[1] == "H" and swing[2] >= prev[2]) or (swing[1] == "L" and swing[2] <= prev[2]):
            out[-1] = swing
    return out


def detect_wave_structure(df):
    ph, pl = find_pivots(df, PIVOT_LEFT, PIVOT_RIGHT)
    swings = alternating_swings(df, ph, pl)
    candidate = None
    start = max(0, len(swings) - 12)
    for i in range(start, len(swings) - 2):
        a, b, c = swings[i:i+3]
        if a[1] == "L" and b[1] == "H" and c[1] == "L":
            size = b[2] - a[2]
            if size <= 0:
                continue
            retr = (b[2] - c[2]) / size
            if 0 < retr < 1:
                candidate = {
                    "wave1_low": a[2],
                    "wave1_high": b[2],
                    "wave2_low": c[2],
                    "wave2_retracement": retr,
                    "wave1_index": a[0],
                    "wave1_high_index": b[0],
                    "wave2_index": c[0]
                }
    return {"found": False} if candidate is None else {"found": True, **candidate}


def fibonacci_levels(low, high):
    if pd.isna(low) or pd.isna(high) or high <= low:
        return {}
    d = high - low
    return {
        "Fib 38.2": high - .382*d,
        "Fib 50": high - .500*d,
        "Fib 61.8": high - .618*d,
        "Fib 78.6": high - .786*d,
        "Fib 127.2": low + 1.272*d,
        "Fib 161.8": low + 1.618*d
    }


def download_stock(symbol):
    try:
        data = yf.download(
            symbol + ".NS",
            period=HISTORY_PERIOD,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False
        )
        if data is None or data.empty:
            return pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data[["Open", "High", "Low", "Close", "Volume"]].dropna()
    except Exception:
        return pd.DataFrame()


def analyse_stock(symbol, df):
    if df.empty:
        return {"Symbol": symbol, "Status": "NO DATA"}
    if len(df) < MIN_HISTORY:
        return {"Symbol": symbol, "Status": "INSUFFICIENT DATA"}

    df = df.copy()
    df["EMA20"] = calculate_ema(df["Close"], 20)
    df["EMA50"] = calculate_ema(df["Close"], 50)
    df["EMA200"] = calculate_ema(df["Close"], 200)
    df["RSI14"] = calculate_rsi(df["Close"])
    df["ATR14"] = calculate_atr(df)
    df["VolumeAvg20"] = df["Volume"].rolling(20).mean()
    df["VolumeRatio"] = df["Volume"] / df["VolumeAvg20"]

    x = df.iloc[-1]
    try:
        close, ema20, ema50, ema200 = map(float, [x["Close"], x["EMA20"], x["EMA50"], x["EMA200"]])
        rsi, atr, volume_ratio = map(float, [x["RSI14"], x["ATR14"], x["VolumeRatio"]])
    except (TypeError, ValueError):
        return {"Symbol": symbol, "Status": "INVALID DATA"}

    bullish = close > ema20 > ema50 > ema200
    bearish = close < ema20 < ema50 < ema200

    wave = detect_wave_structure(df)
    if wave["found"]:
        wave1_high = wave["wave1_high"]
        wave2_low = wave["wave2_low"]
        retr = wave["wave2_retracement"]
        breakout = close > wave1_high
    else:
        wave1_high = wave2_low = retr = np.nan
        breakout = False

    volume_ok = volume_ratio >= VOLUME_MULTIPLIER
    rsi_buy = RSI_BUY_MIN <= rsi <= RSI_BUY_MAX
    rsi_sell = RSI_SELL_MIN <= rsi <= RSI_SELL_MAX
    wave2_ok = wave["found"] and retr <= MAX_WAVE2_RETRACEMENT

    buy_score = sum([bullish, breakout, volume_ok, rsi_buy, wave2_ok])
    sell_score = sum([bearish, volume_ok, rsi_sell])

    if buy_score >= 4 and breakout and volume_ok:
        signal = "SELECTED BUY"
    elif sell_score >= 3 and bearish:
        signal = "SELECTED SELL"
    elif buy_score >= 3:
        signal = "WATCH BUY"
    elif sell_score >= 2:
        signal = "WATCH SELL"
    else:
        signal = "NOT SELECTED"

    entry = close
    sl = t1 = t2 = rr = np.nan

    if signal in ("SELECTED BUY", "WATCH BUY"):
        sl = min(wave2_low, close - 1.5*atr) if wave["found"] else close - 2*atr
        risk = entry - sl
        if risk > 0:
            t1, t2, rr = entry + 2*risk, entry + 3*risk, 2.0
    elif signal in ("SELECTED SELL", "WATCH SELL"):
        sl = max(wave1_high, close + 1.5*atr) if wave["found"] else close + 2*atr
        risk = sl - entry
        if risk > 0:
            t1, t2, rr = entry - 2*risk, entry - 3*risk, 2.0

    fib = fibonacci_levels(wave2_low, wave1_high) if wave["found"] else {}

    reason = "; ".join([
        "Trend=" + ("OK" if bullish else "BEARISH" if bearish else "MIXED"),
        "Breakout=" + ("YES" if breakout else "NO"),
        "Volume=" + ("OK" if volume_ok else "WEAK"),
        f"RSI={rsi:.1f}",
        "Wave2=" + ("OK" if wave2_ok else "FAIL")
    ])

    return {
        "Symbol": symbol, "Status": "OK", "Signal": signal,
        "Score": buy_score if "BUY" in signal else sell_score,
        "Close": close,
        "Trend": "BULLISH" if bullish else "BEARISH" if bearish else "MIXED",
        "Wave Setup": ("WAVE 3 CANDIDATE" if breakout else "WAVE 2 / PRE-BREAKOUT") if wave["found"] else "NO CLEAN STRUCTURE",
        "Wave-2 Retracement %": retr*100 if wave["found"] else np.nan,
        "Wave-1 High": wave1_high, "Wave-2 Low": wave2_low,
        "Breakout": "YES" if breakout else "NO",
        "RSI14": rsi, "EMA20": ema20, "EMA50": ema50, "EMA200": ema200,
        "Volume Ratio": volume_ratio, "ATR14": atr,
        "Entry": entry, "Stop Loss": sl, "Target 1 (2R)": t1,
        "Target 2 (3R)": t2, "Risk/Reward": rr,
        "Futures OI": "NOT LOADED", "Option PCR": "NOT LOADED", "Option IV": "NOT LOADED",
        **fib, "Reason": reason
    }


def read_symbols():
    symbols = list(EMBEDDED_SYMBOLS)
    if not symbols:
        raise ValueError("Embedded Nifty 500 symbol list is empty.")
    return symbols


def scan_all_stocks(symbols):
    results = []
    total = len(symbols)
    print("\n" + "="*70)
    print("NIFTY 500 SCANNER")
    print("="*70)
    print(f"Stocks: {total}")
    print(f"Started: {datetime.now():%d-%b-%Y %H:%M:%S}")
    print("="*70)

    def process(s):
        return analyse_stock(s, download_stock(s))

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process, s): s for s in symbols}
        for n, future in enumerate(as_completed(futures), 1):
            symbol = futures[future]
            try:
                result = future.result()
            except Exception as e:
                result = {"Symbol": symbol, "Status": "ERROR: " + str(e)}
            results.append(result)
            print(f"[{n:3d}/{total}] {symbol:<15} {result.get('Signal', result.get('Status',''))}")
    return pd.DataFrame(results)


def rank_results(df):
    if "Signal" not in df.columns:
        return df
    ranking = {"SELECTED BUY":1, "SELECTED SELL":2, "WATCH BUY":3, "WATCH SELL":4, "NOT SELECTED":5}
    out = df.copy()
    out["_Rank"] = out["Signal"].map(ranking).fillna(9)
    return out.sort_values(["_Rank", "Score"], ascending=[True, False]).drop(columns="_Rank")


def save_excel(df):
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="All Results", index=False)
        if "Signal" in df.columns:
            df[df.Signal == "SELECTED BUY"].to_excel(writer, sheet_name="SELECTED BUY", index=False)
            df[df.Signal == "SELECTED SELL"].to_excel(writer, sheet_name="SELECTED SELL", index=False)
            df[df.Signal.isin(["WATCH BUY","WATCH SELL"])].to_excel(writer, sheet_name="WATCH", index=False)
        pd.DataFrame({"Rule": [
            "Bull trend = Close > EMA20 > EMA50 > EMA200",
            "Wave structure = confirmed L-H-L pivot sequence",
            "Wave 2 retracement must remain below 100%",
            "Wave 3 breakout = Close above Wave-1 high",
            "Breakout volume = Volume >= 1.5 x 20-day average",
            "BUY RSI = 55 to 75; SELL RSI = 25 to 45",
            "Selected BUY = score >= 4 + breakout + volume",
            "Selected SELL = score >= 3 + bearish EMA alignment",
            "Targets = 2R and 3R; stop uses Wave-2 / ATR",
            "Elliott Wave is heuristic, not objectively validated",
            "Futures OI = NOT LOADED; Option PCR = NOT LOADED; Option IV = NOT LOADED"
        ]}).to_excel(writer, sheet_name="Logic", index=False)


def print_summary(df):
    print("\n" + "="*70)
    print("SCAN COMPLETE")
    print("="*70)
    if "Signal" not in df.columns:
        print("No signals generated.")
        return
    counts = df["Signal"].value_counts()
    for s in ["SELECTED BUY","SELECTED SELL","WATCH BUY","WATCH SELL","NOT SELECTED"]:
        print(f"{s:<20}: {counts.get(s,0)}")
    selected = df[df.Signal.isin(["SELECTED BUY","SELECTED SELL"])]
    if not selected.empty:
        cols = ["Symbol","Signal","Score","Close","RSI14","Volume Ratio","Entry","Stop Loss","Target 1 (2R)","Target 2 (3R)","Risk/Reward"]
        print("\nTOP SELECTED SETUPS")
        print(selected[cols].head(20).to_string(index=False))
    print(f"\nExcel result: {OUTPUT_FILE}")
    print(f"Finished: {datetime.now():%d-%b-%Y %H:%M:%S}")


def main():
    symbols = read_symbols()
    if len(symbols) != 500:
        print(f"WARNING: symbol file contains {len(symbols)} stocks, not 500.")
    df = rank_results(scan_all_stocks(symbols))
    numeric = ["Close","Wave-2 Retracement %","Wave-1 High","Wave-2 Low","RSI14","EMA20","EMA50","EMA200","Volume Ratio","ATR14","Fib 38.2","Fib 50","Fib 61.8","Fib 78.6","Fib 127.2","Fib 161.8","Entry","Stop Loss","Target 1 (2R)","Target 2 (3R)","Risk/Reward"]
    for c in numeric:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").round(2)
    save_excel(df)
    print_summary(df)


if __name__ == "__main__":
    main()
