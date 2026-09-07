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
    """Get the latest result file and its timestamp."""
    pattern = RESULT_DIR / f"{kind}_*.csv"
    files = sorted(glob.glob(str(pattern)), key=lambda x: Path(x).stat().st_mtime)
    
    if not files:
        return None, None
    
    latest_file = files[-1]
    try:
        df = pd.read_csv(latest_file)
        # Extract timestamp from filename (format: kind_YYYYMMDD_HHMMSS.csv)
        filename = Path(latest_file).stem
        parts = filename.split('_')
        if len(parts) >= 3:
            date_part = parts[-2]
            time_part = parts[-1]
            timestamp_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
        else:
            timestamp_str = "Unknown"
        return df, timestamp_str
    except Exception:
        return None, None


def get_all_results(kind):
    """Get all available result files for a given scan kind."""
    pattern = RESULT_DIR / f"{kind}_*.csv"
    files = sorted(glob.glob(str(pattern)), key=lambda x: Path(x).stat().st_mtime, reverse=True)
    return files


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
    df, scan_time = get_latest_result_info("scan_0930")
    if df is None or df.empty:
        st.info("09:30 scan result is not available yet.")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✅ Loaded {len(df)} stocks")
        with col2:
            st.caption(f"📅 Scanned at: {scan_time}")
        
        # Get all available scans for this kind
        all_files = get_all_results("scan_0930")
        if len(all_files) > 1:
            with st.expander(f"📊 View Previous Scans ({len(all_files) - 1} more)"):
                selected_file = st.selectbox(
                    "Select a previous scan",
                    all_files[1:],  # Skip the latest one
                    format_func=lambda x: Path(x).stem.replace('scan_0930_', ''),
                    key="prev_0930"
                )
                if selected_file:
                    prev_df = load_result_file(selected_file)
                    filename = Path(selected_file).stem
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        date_part = parts[-2]
                        time_part = parts[-1]
                        prev_time = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                    else:
                        prev_time = "Unknown"
                    st.caption(f"📅 Scanned at: {prev_time}")
                    st.dataframe(prev_df, use_container_width=True, hide_index=True)
        
        signal = st.selectbox("Signal", ["ALL", "SELECTED BUY", "SELECTED SELL", "WATCH BUY", "WATCH SELL", "NOT SELECTED"], key="s1")
        view = df if (signal == "ALL" or "Signal" not in df.columns) else df[df["Signal"] == signal]
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.download_button("Download CSV", view.to_csv(index=False), "Nifty500_0930.csv", "text/csv")

with tab2:
    df, scan_time = get_latest_result_info("scan_1000")
    if df is None or df.empty:
        st.info("10:00 confirmation scan result is not available yet.")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✅ Loaded {len(df)} stocks")
        with col2:
            st.caption(f"📅 Scanned at: {scan_time}")
        
        # Get all available scans for this kind
        all_files = get_all_results("scan_1000")
        if len(all_files) > 1:
            with st.expander(f"📊 View Previous Scans ({len(all_files) - 1} more)"):
                selected_file = st.selectbox(
                    "Select a previous scan",
                    all_files[1:],  # Skip the latest one
                    format_func=lambda x: Path(x).stem.replace('scan_1000_', ''),
                    key="prev_1000"
                )
                if selected_file:
                    prev_df = load_result_file(selected_file)
                    filename = Path(selected_file).stem
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        date_part = parts[-2]
                        time_part = parts[-1]
                        prev_time = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                    else:
                        prev_time = "Unknown"
                    st.caption(f"📅 Scanned at: {prev_time}")
                    st.dataframe(prev_df, use_container_width=True, hide_index=True)
        
        signal = st.selectbox("Signal", ["ALL", "CONFIRMED BUY", "CONFIRMED SELL", "NEW BUY", "NEW SELL", "REJECTED", "WATCH"], key="s2")
        view = df if (signal == "ALL" or "Confirmation" not in df.columns) else df[df["Confirmation"] == signal]
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.download_button("Download CSV", view.to_csv(index=False), "Nifty500_1000_confirmation.csv", "text/csv")

st.divider()
st.caption(f"Dashboard refreshed: {datetime.now():%d-%b-%Y %H:%M:%S}")
