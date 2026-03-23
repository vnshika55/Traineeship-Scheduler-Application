import streamlit as st
import pandas as pd
from scheduler import (
    generate_schedule,
    load_qualifications,
    load_units,
    generate_pdf
)

st.set_page_config(page_title="Traineeship Scheduler", layout="wide")

st.title("📅 Traineeship Class Schedule Generator")

# Load qualifications
qual_df = load_qualifications()

qualification_display = {
    f"{row['qualification_code']} - {row['qualification_name']}": row['qualification_code']
    for _, row in qual_df.iterrows()
}

# ------------------------
# Form Inputs
# ------------------------

learner_name = st.text_input("Learner Name")

state = st.selectbox("State", ["NSW", "ACT"])

qualification_selected = st.selectbox(
    "Qualification",
    list(qualification_display.keys())
)

start_date = st.date_input("Start Date")
contract_end_date = st.date_input("Training Contract End Date")

gap_option = st.selectbox(
    "Gap Between Units",
    ["2weeks", "3weeks", "4weeks", "month"]
)

qualification_code = qualification_display[qualification_selected]

# Load units
units_df = load_units(qualification_code)
unit_codes = units_df["unit_code"].tolist()

credit_transfer_units = st.multiselect(
    "Credit Transfer Units (if any)",
    unit_codes
)

# ------------------------
# Generate Schedule
# ------------------------

if st.button("Generate Schedule"):

    schedule = generate_schedule(
        start_date,
        qualification_code,
        state,
        gap_option,
        credit_transfer_units
    )

    # ------------------------
    # DISPLAY FORMAT
    # ------------------------
    schedule_display = schedule.copy()
    schedule_display["Start Date"] = pd.to_datetime(schedule_display["Start Date"]).dt.strftime("%d/%m/%Y")
    schedule_display["End Date"] = pd.to_datetime(schedule_display["End Date"]).dt.strftime("%d/%m/%Y")

    st.subheader("📄 Generated Class Schedule")

    st.write(f"**Learner:** {learner_name}")
    st.write(f"**Qualification:** {qualification_selected}")
    st.write(f"**State:** {state}")

    st.dataframe(schedule_display, use_container_width=True)

    # Validation
    last_end_date = pd.to_datetime(schedule["End Date"]).max()

    if last_end_date > pd.to_datetime(contract_end_date):
        st.warning("⚠️ Schedule exceeds Training Contract End Date!")

    # ------------------------
    # CSV DOWNLOAD
    # ------------------------
    st.download_button(
        label="📥 Download Schedule (CSV)",
        data=schedule_display.to_csv(index=False),
        file_name=f"{learner_name}_schedule.csv",
        mime="text/csv"
    )

    # ------------------------
    # PDF DOWNLOAD
    # ------------------------
    pdf_file = generate_pdf(
        schedule,   # ✅ pass ORIGINAL (not formatted)
        learner_name,
        qualification_selected
    )

    st.download_button(
        label="📄 Download Professional Schedule PDF",
        data=pdf_file,
        file_name=f"{learner_name}_schedule.pdf",
        mime="application/pdf"
    )