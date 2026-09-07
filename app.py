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


def load_latest_result(kind):
    """Load the most recent timestamped result file for a given scan kind."""
    pattern = RESULT_DIR / f"{kind}_*.csv"
    files = sorted(glob.glob(str(pattern)), key=lambda x: Path(x).stat().st_mtime)
    
    if not files:
        return pd.DataFrame()
    
    latest_file = files[-1]  # Get the most recent file
    try:
        return pd.read_csv(latest_file)
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
    """Run an external scan script if present. Returns (success: bool, message: str)."""
    script = find_scan_script()
    if not script:
        return False, "No scan script found. Add a scan.py (or scanner.py / run_scans.py) to the app directory that accepts a kind argument (e.g. scan_0930)."

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RESULT_DIR / f"{kind}_{timestamp}.csv"
    
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

        # If all scans succeeded, reload the app to show latest results
        if all_ok:
            st.experimental_rerun()


tab1, tab2 = st.tabs(["09:30 Initial Scan", "10:00 Confirmation"])

with tab1:
    df = load_latest_result("scan_0930")
    if df.empty:
        st.info("09:30 scan result is not available yet.")
    else:
        st.success(f"Loaded {len(df)} stocks")
        signal = st.selectbox("Signal", ["ALL", "SELECTED BUY", "SELECTED SELL", "WATCH BUY", "WATCH SELL", "NOT SELECTED"], key="s1")
        view = df if (signal == "ALL" or "Signal" not in df.columns) else df[df["Signal"] == signal]
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.download_button("Download CSV", view.to_csv(index=False), "Nifty500_0930.csv", "text/csv")

with tab2:
    df = load_latest_result("scan_1000")
    if df.empty:
        st.info("10:00 confirmation scan result is not available yet.")
    else:
        st.success(f"Loaded {len(df)} stocks")
        signal = st.selectbox("Signal", ["ALL", "CONFIRMED BUY", "CONFIRMED SELL", "NEW BUY", "NEW SELL", "REJECTED", "WATCH"], key="s2")
        view = df if (signal == "ALL" or "Confirmation" not in df.columns) else df[df["Confirmation"] == signal]
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.download_button("Download CSV", view.to_csv(index=False), "Nifty500_1000_confirmation.csv", "text/csv")

st.divider()
st.caption(f"Dashboard refreshed: {datetime.now():%d-%b-%Y %H:%M:%S}")
