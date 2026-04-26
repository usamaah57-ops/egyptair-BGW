import streamlit as st
from modules.database import (
    init_db, save_service, load_services,
    clear_services, archive_services
)
from datetime import datetime

init_db()

st.title("✈️ New Flight Operations")

st.write("This page will contain the full flight operations workflow.")

# Staff login
if 'staff_confirmed' not in st.session_state:
    st.session_state.staff_confirmed = False

if 'current_staff' not in st.session_state:
    st.session_state.current_staff = ""

if not st.session_state.staff_confirmed:
    name_input = st.text_input("Enter your full name:")
    if st.button("Confirm and Enter"):
        if name_input.strip():
            st.session_state.current_staff = name_input.strip()
            st.session_state.staff_confirmed = True
            st.rerun()
        else:
            st.error("Please enter your name to continue.")
    st.stop()

st.write(f"👷 Current Staff: **{st.session_state.current_staff}**")

# Flight inputs
flight = st.text_input("Flight Number", value="MS616").upper()
reg = st.text_input("Registration (Reg)", value="SU-").upper()

st.divider()

# Add new flight
if st.button("➕ Add New Flight", use_container_width=True):
    clear_services()
    st.rerun()

# Services list
services_labels = [
    ("⏱ Chocks ON", "CHOCKS_ON"), ("⚡ GPU Arrival", "GPU_ARRIVAL"),
    ("🔌 APU Start", "APU_START"), ("🛠 Air Starter", "AIR_STARTER"),
    ("📦 FWD Open", "FWD_OPEN"), ("📦 FWD Close", "FWD_CLOSE"),
    ("📦 AFT Open", "AFT_OPEN"), ("📦 AFT Close", "AFT_CLOSE"),
    ("🚛 Fuel Arrival", "FUEL_ARRIVAL"), ("⛽ Fuel End", "FUEL_END"),
    ("🧹 Cleaning START", "CLEANING_START"), ("✨ Cleaning END", "CLEANING_END"),
    ("🚶 First Pax", "FIRST_PAX"), ("🏁 Last Pax", "LAST_PAX"),
    ("📑 Loadsheet", "LOADSHEET"), ("🚪 Close Door", "CLOSE_DOOR"),
    ("🚜 Pushback Truck", "PUSHBACK_TRUCK"), ("🚀 Push Back", "PUSH_BACK")
]

current_shared_times = load_services()
cols = st.columns(2)

# Display buttons or recorded times
for i, (label, key) in enumerate(services_labels):
    if key in current_shared_times:
        recorded = current_shared_times[key]
        cols[i % 2].success(f"{label}\n{recorded['time']} ({recorded['staff']})")
    else:
        if cols[i % 2].button(label, key=key, use_container_width=True):
            now_t = datetime.now().strftime("%H:%M")
            save_service(key, now_t, st.session_state.current_staff)
            st.rerun()

st.divider()

# Final report
if st.button("📧 Send Final Report and Archive Data", type="primary", use_container_width=True):
    current_shared_times = load_services()
    if not current_shared_times:
        st.warning("⚠️ No data available!")
    else:
        ok = archive_services(flight, reg)
        if ok:
            clear_services()
            st.success("✅ Report archived successfully.")
            st.balloons()
            st.rerun()
        else:
            st.warning("This flight is already archived for today.")
