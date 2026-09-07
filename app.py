import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import subprocess
import sys
import glob

st.set_page_config(page_title="Nifty 500 Elliott Scanner", page_icon="📈", layout="wide")

st.title("📈 Nifty 500 Elliott Wave Scanner")
st.caption("Mobile dashboard • 09:30 initial scan • 10:00 confirmation scan")

RESULT_DIR = Path("results")
RESULT_DIR.mkdir(exist_ok=True)


def get_latest_result_info(kind):
    """Get the latest (live) result file and its timestamp (file mtime)."""
    filepath = RESULT_DIR / f"{kind}_latest.csv"
    if not filepath.exists():
        return None, None
    try:
        df = pd.read_csv(filepath)
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        return df, mtime
    except Exception:
        return None, None


def load_result_file(filepath):
    """Load a specific result file."""
    try:
        return pd.read_csv(filepath)
    except Exception:
        return pd.DataFrame()


def find_scan_script():
    # look for common scan script names in the app directory
    candidates = ["scan.py", "scanner.py", "run_scans.py", "run_scan.py", "scan_all.py"]
    for c in candidates:
        if Path(c).exists():
            return c
    return None


def run_scan(kind):
    """Run an external scan script if present. Returns (success: bool, message: str).
    This writes results to a fixed 'latest' filename so we don't keep timestamped history."""
    script = find_scan_script()
    if not script:
        return False, "No scan script found. Add a scan.py (or scanner.py / run_scans.py) to the app directory that accepts a kind argument (e.g. scan_0930) and writes CSV to the provided output path."

    # Use a fixed filename for live results (overwrite existing)
    output_file = RESULT_DIR / f"{kind}_latest.csv"

    cmd = [sys.executable, script, kind, str(output_file)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode == 0:
            return True, proc.stdout.strip() or f"Scan completed successfully. Results saved to {output_file.name}"
        else:
            # include stderr for diagnostics
            msg = proc.stderr.strip() or proc.stdout.strip() or f"Scan exited with code {proc.returncode}"
            return False, msg
    except subprocess.TimeoutExpired:
        return False, f"Scan timed out after 5 minutes"
    except Exception as e:
        return False, str(e)


# --- Scan Now UI ---
with st.expander("Run scan now"):
    scan_choice = st.selectbox("Choose scan to run", ["0930 - Initial Scan", "1000 - Confirmation", "Both (Live Scan at Time)"], key="scan_choice")
    if st.button("Scan Now", key="scan_now"):
        kinds = []
        if scan_choice.startswith("0930"):
            kinds = ["scan_0930"]
        elif scan_choice.startswith("1000"):
            kinds = ["scan_1000"]
        else:  # Both
            kinds = ["scan_0930", "scan_1000"]

        all_ok = True
        for k in kinds:
            with st.spinner(f"Running {k}..."):
                ok, msg = run_scan(k)
                if ok:
                    st.success(f"{k}: {msg}")
                else:
                    all_ok = False
                    st.error(f"{k}: {msg}")

        # If all scans succeeded, reload the app to show latest live results
        if all_ok:
            st.experimental_rerun()


tab1, tab2 = st.tabs(["09:30 Initial Scan", "10:00 Confirmation"])

with tab1:
    df, scan_time = get_latest_result_info("scan_0930")
    if df is None or df.empty:
        st.info("09:30 live scan result is not available yet.")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✅ Loaded {len(df)} stocks (live)")
        with col2:
            st.caption(f"📅 Live scanned at: {scan_time}")

        # Show the live data only (no previous scans)
        signal = st.selectbox("Signal", ["ALL", "SELECTED BUY", "SELECTED SELL", "WATCH BUY", "WATCH SELL", "NOT SELECTED"], key="s1")
        view = df if (signal == "ALL" or "Signal" not in df.columns) else df[df["Signal"] == signal]
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.download_button("Download CSV (live)", view.to_csv(index=False), "Nifty500_0930_live.csv", "text/csv")

with tab2:
    df, scan_time = get_latest_result_info("scan_1000")
    if df is None or df.empty:
        st.info("10:00 live confirmation scan result is not available yet.")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✅ Loaded {len(df)} stocks (live)")
        with col2:
            st.caption(f"📅 Live scanned at: {scan_time}")

        # Show the live data only (no previous scans)
        signal = st.selectbox("Signal", ["ALL", "CONFIRMED BUY", "CONFIRMED SELL", "NEW BUY", "NEW SELL", "REJECTED", "WATCH"], key="s2")
        view = df if (signal == "ALL" or "Confirmation" not in df.columns) else df[df["Confirmation"] == signal]
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.download_button("Download CSV (live)", view.to_csv(index=False), "Nifty500_1000_confirmation_live.csv", "text/csv")

st.divider()
st.caption(f"Dashboard refreshed: {datetime.now():%d-%b-%Y %H:%M:%S}")
