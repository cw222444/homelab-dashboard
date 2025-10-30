import streamlit as st
import psutil
import requests
import pandas as pd
import time
from datetime import datetime

# --------------------------
# CONFIGURATION
# --------------------------
SERVICES = {
    "Website": "https://example.com",
    "Router": "http://192.168.1.1",
}
REFRESH_INTERVAL = 20  # seconds between updates
MAX_HISTORY = 30      # number of points to keep in charts

# --------------------------
# FUNCTIONS
# --------------------------
def check_service(url: str) -> bool:
    """Check if a service is reachable."""
    try:
        r = requests.get(url, timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def get_system_stats():
    """Collect current system stats."""
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    return cpu, mem, disk

# --------------------------
# STREAMLIT SETUP
# --------------------------
st.set_page_config(
    page_title="Homelab Dashboard",
    page_icon="🖥️",
    layout="wide",
)

st.title("🖥️ Homelab Monitoring Dashboard")
st.caption("Real-time uptime and system stats")

# Initialize session state for charts
if "stats_history" not in st.session_state:
    st.session_state["stats_history"] = pd.DataFrame(columns=["Time", "CPU", "Memory", "Disk"])

placeholder = st.empty()

# --------------------------
# MAIN LOOP
# --------------------------
while True:
    # Get system stats
    cpu, mem, disk = get_system_stats()

    # Check uptime
    uptime_results = {
        name: "🟢 UP" if check_service(url) else "🔴 DOWN"
        for name, url in SERVICES.items()
    }

    # Add to history
    new_row = pd.DataFrame({
        "Time": [datetime.now().strftime("%H:%M:%S")],
        "CPU": [cpu],
        "Memory": [mem],
        "Disk": [disk],
    })
    st.session_state["stats_history"] = (
        pd.concat([st.session_state["stats_history"], new_row])
        .tail(MAX_HISTORY)
        .reset_index(drop=True)
    )

    # --------------------------
    # RENDER DASHBOARD
    # --------------------------
    with placeholder.container():
        col1, col2, col3 = st.columns(3)
        col1.metric("CPU Usage", f"{cpu:.1f} %")
        col2.metric("Memory Usage", f"{mem:.1f} %")
        col3.metric("Disk Usage", f"{disk:.1f} %")

        st.markdown("### 📊 System Trends (Last Few Updates)")
        st.line_chart(
            st.session_state["stats_history"].set_index("Time")[["CPU", "Memory", "Disk"]],
            use_container_width=True,
        )

        st.markdown("### 📡 Uptime Checks")
        uptime_table = pd.DataFrame(
            [{"Service": k, "Status": v, "URL": SERVICES[k]} for k, v in uptime_results.items()]
        )
        st.dataframe(uptime_table, width="stretch", hide_index=True)

        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    time.sleep(REFRESH_INTERVAL)
    st.rerun()
