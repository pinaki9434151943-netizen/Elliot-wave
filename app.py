import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Nifty 500 Elliott Scanner", page_icon="📈", layout="wide")

st.title("📈 Nifty 500 Elliott Wave Scanner")
st.caption("Mobile dashboard • 09:30 initial scan • 10:00 confirmation scan")

RESULT_DIR = Path("results")
RESULT_DIR.mkdir(exist_ok=True)

def load_result(kind):
    p = RESULT_DIR / f"{kind}.csv"
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(p)
    except Exception:
        return pd.DataFrame()

tab1, tab2 = st.tabs(["09:30 Initial Scan", "10:00 Confirmation"])

with tab1:
    df = load_result("scan_0930")
    if df.empty:
        st.info("09:30 scan result is not available yet.")
    else:
        st.success(f"Loaded {len(df)} stocks")
        signal = st.selectbox("Signal", ["ALL", "SELECTED BUY", "SELECTED SELL", "WATCH BUY", "WATCH SELL", "NOT SELECTED"], key="s1")
        view = df if signal == "ALL" or "Signal" not in df.columns else df[df["Signal"] == signal]
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.download_button("Download CSV", view.to_csv(index=False), "Nifty500_0930.csv", "text/csv")

with tab2:
    df = load_result("scan_1000")
    if df.empty:
        st.info("10:00 confirmation scan result is not available yet.")
    else:
        st.success(f"Loaded {len(df)} stocks")
        signal = st.selectbox("Signal", ["ALL", "CONFIRMED BUY", "CONFIRMED SELL", "NEW BUY", "NEW SELL", "REJECTED", "WATCH"], key="s2")
        view = df if signal == "ALL" or "Confirmation" not in df.columns else df[df["Confirmation"] == signal]
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.download_button("Download CSV", view.to_csv(index=False), "Nifty500_1000_confirmation.csv", "text/csv")

st.divider()
st.caption(f"Dashboard refreshed: {datetime.now():%d-%b-%Y %H:%M:%S}")
