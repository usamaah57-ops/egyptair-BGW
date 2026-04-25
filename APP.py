import streamlit as st
import sqlite3
from datetime import datetime
from fpdf import FPDF
from io import BytesIO
import os

DB_FILE = "flight_data.db"

# -------------------- DOCUMENT TYPES --------------------

DOC_TYPES = {
    "📑 Loadsheet": "loadsheet",
    "📘 Load Instruction": "load_instruction",
    "⛽ Fuel Receipt": "fuel_receipt",
    "🛢 Fuel Info Sheet": "fuel_info",
    "🛄 GD": "gd",
    "🛫 Flight Plan": "flight_plan"
}

DOC_FOLDER = "docs"
os.makedirs(DOC_FOLDER, exist_ok=True)

# -------------------- DATABASE --------------------

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS services (
            key TEXT PRIMARY KEY,
            time TEXT,
            staff TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS archive (
            flight TEXT,
            reg TEXT,
            date TEXT,
            key TEXT,
            time TEXT,
            staff TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_service(key, time, staff):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO services (key, time, staff) VALUES (?, ?, ?)", (key, time, staff))
    conn.commit()
    conn.close()


def load_services():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT key, time, staff FROM services")
    rows = c.fetchall()
    conn.close()
    return {r[0]: {"time": r[1], "staff": r[2]} for r in rows}


def clear_services():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM services")
    conn.commit()
    conn.close()


def archive_services(flight, reg):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    date = datetime.now().strftime("%d/%m/%Y")

    c.execute("SELECT COUNT(*) FROM archive WHERE flight=? AND reg=? AND date=?", (flight, reg, date))
    exists = c.fetchone()[0]

    if exists > 0:
        st.warning(f"⚠️ Flight {flight} ({reg}) already archived for {date}.")
        conn.close()
        return False

    services = load_services()
    for k, v in services.items():
        c.execute("INSERT INTO archive (flight, reg, date, key, time, staff) VALUES (?, ?, ?, ?, ?, ?)",
                  (flight, reg, date, k, v['time'], v['staff']))

    conn.commit()
    conn.close()
    return True


def load_archive():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT flight, reg, date, key, time, staff FROM archive ORDER BY date DESC")
    rows = c.fetchall()
    conn.close()
    return rows

# -------------------- PDF GENERATOR (WITH DOCUMENT PAGES) --------------------

def generate_pdf(flight, reg, date, records):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Baghdad Station Operations Report", ln=True, align="C")

    pdf.set_font("Arial", "", 12)
    pdf.ln(5)
    pdf.cell(0, 8, f"Flight: {flight}", ln=True)
    pdf.cell(0, 8, f"Registration: {reg}", ln=True)
    pdf.cell(0, 8, f"Date: {date}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 8, "Service", border=1)
    pdf.cell(40, 8, "Time", border=1)
    pdf.cell(80, 8, "Staff", border=1, ln=True)

    pdf.set_font("Arial", "", 11)
    for r in records:
        pdf.cell(60, 8, r[3], border=1)
        pdf.cell(40, 8, r[4], border=1)
        pdf.cell(80, 8, r[5], border=1, ln=True)

    # ---- Append document pages if exist ----
    try:
        date_obj = datetime.strptime(date, "%d/%m/%Y")
        date_key = date_obj.strftime("%Y%m%d")
    except:
        date_key = date.replace("/", "")

    for label, key in DOC_TYPES.items():
        img_path = os.path.join(DOC_FOLDER, f"{key}_{flight}_{date_key}.jpg")
        if os.path.exists(img_path):
            pdf.add_page()
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, label.replace("📑","").replace("📘","").replace("⛽","").replace("🛢","").replace("🛄","").replace("🛫","").strip(), ln=True)
            pdf.ln(5)
            pdf.image(img_path, x=10, y=25, w=180)

    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    buffer = BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer

# -------------------- INIT --------------------

init_db()

st.set_page_config(page_title="Baghdad Station Operations", page_icon="✈️", layout="centered")

# -------------------- HEADER --------------------

st.image("egyptair_plane.jpg.webp", use_column_width=True)
st.title("✈️ Baghdad Station Operations")

# -------------------- STAFF LOGIN --------------------

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

# -------------------- FLIGHT INFO --------------------

flight = st.text_input("Flight Number", value="MS616").upper()
reg = st.text_input("Registration (Reg)", value="SU-").upper()

st.divider()

# -------------------- ADD NEW FLIGHT --------------------

if st.button("➕ Add New Flight", use_container_width=True):
    clear_services()
    st.rerun()

# -------------------- SERVICES --------------------

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

# -------------------- DOCUMENT SCANNER (CAMERA + PDF + LINK TO FLIGHT) --------------------

st.subheader("📄 Document Scanner")

doc_cols = st.columns(3)
selected_doc = None

for i, (label, key) in enumerate(DOC_TYPES.items()):
    if doc_cols[i % 3].button(label, use_container_width=True, key=f"docbtn_{key}"):
        selected_doc = key

if selected_doc:
    st.info(f"📸 Capture {selected_doc.replace('_',' ').title()} for Flight {flight}")
    photo = st.camera_input("Take a photo of the document")

    if photo is not None:
        st.success("Document captured successfully!")

        # Normalize date key for filename
        today = datetime.now()
        date_key = today.strftime("%Y%m%d")

        img_path = os.path.join(DOC_FOLDER, f"{selected_doc}_{flight}_{date_key}.jpg")
        with open(img_path, "wb") as f:
            f.write(photo.getbuffer())

        st.image(photo, caption="Captured Document", use_column_width=True)

        # Create single-page PDF for this document (for direct download)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, selected_doc.replace('_',' ').title(), ln=True)
        pdf.ln(5)
        pdf.image(img_path, x=10, y=25, w=180)

        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        pdf_buffer = BytesIO(pdf_bytes)
        pdf_buffer.seek(0)

        filename = f"{selected_doc}_{flight}_{today.strftime('%d-%m-%Y')}.pdf"

        st.download_button(
            label="📄 Download Document PDF",
            data=pdf_buffer,
            file_name=filename,
            mime="application/pdf"
        )

st.divider()

# -------------------- FINAL REPORT BUTTON --------------------

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

# -------------------- ARCHIVE VIEWER + PDF WITH DOCUMENT PAGES --------------------

st.divider()
st.subheader("📂 Archived Reports")

archive = load_archive()

if archive:
    grouped = {}
    for row in archive:
        key = (row[0], row[1], row[2])
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(row)

    for (aflight, areg, adate), records in grouped.items():
        st.write(f"✈️ Flight {aflight} | Reg {areg} | Date {adate}")

        pdf_buffer = generate_pdf(aflight, areg, adate, records)

        st.download_button(
            label="📄 Download Full Report PDF (with documents)",
            data=pdf_buffer,
            file_name=f"{aflight}_{areg}_{adate.replace('/','-')}.pdf",
            mime="application/pdf"
        )

        for r in records:
            st.write(f"- {r[3]} at {r[4]} by {r[5]}")

        st.markdown("---")
else:
    st.info("No archived reports yet.")
