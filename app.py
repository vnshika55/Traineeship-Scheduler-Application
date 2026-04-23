import streamlit as st
import pandas as pd

from scheduler import (
    generate_schedule,
    load_qualifications,
    load_units,
    generate_pdf
)

from database import *

st.set_page_config(page_title="Traineeship Scheduler", layout="wide")

create_tables()
create_default_admin()

# -------------------------
# SESSION
# -------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None


# -------------------------
# LOGIN
# -------------------------

def login():

    st.title("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        user = get_user(email, password)

        if user:
            st.session_state.logged_in = True
            st.session_state.user = user[1]
            st.session_state.role = user[3]
            st.rerun()
        else:
            st.error("Invalid credentials")


# -------------------------
# ADMIN PANEL
# -------------------------

def admin_panel():

    st.title("Admin Panel")

    st.subheader("Add User")

    col1, col2, col3 = st.columns(3)

    email = col1.text_input("Email")
    password = col2.text_input("Password")
    role = col3.selectbox("Role", ["user", "admin"])

    if st.button("Add User"):
        add_user(email, password, role)
        st.success("User Added")
        st.rerun()

    st.divider()

    st.subheader("Users")

    users = get_users()

    for user in users:

        col1, col2, col3, col4 = st.columns([3,1,1,1])

        col1.write(user[1])
        col2.write(user[3])
        col3.write("Active" if user[4] else "Disabled")

        if col4.button("Toggle", key=f"toggle{user[0]}"):
            toggle_user(user[0])
            st.rerun()

        if st.button("Delete", key=f"delete{user[0]}"):
            delete_user(user[0])
            st.rerun()


# -------------------------
# SCHEDULER
# -------------------------

def scheduler_ui():

    st.title("Traineeship Scheduler")

    qual_df = load_qualifications()

    qualification_display = {
        f"{row['qualification_code']} - {row['qualification_name']}":
        row['qualification_code']
        for _, row in qual_df.iterrows()
    }

    col1, col2 = st.columns(2)

    with col1:
        learner_name = st.text_input("Learner Name")
        state = st.selectbox("State", ["NSW", "ACT"])

    with col2:
        qualification_selected = st.selectbox(
            "Qualification",
            list(qualification_display.keys())
        )

        gap_option = st.selectbox(
            "Gap Between Units",
            ["2weeks", "3weeks", "4weeks", "month"]
        )

    qualification_code = qualification_display[qualification_selected]

    col3, col4 = st.columns(2)

    with col3:
        start_date = st.date_input("Start Date")

    with col4:
        contract_end_date = st.date_input("Training Contract End Date")

    units_df = load_units(qualification_code)
    unit_codes = units_df["unit_code"].tolist()

    credit_transfer_units = st.multiselect(
        "Credit Transfer Units",
        unit_codes
    )

    if credit_transfer_units:
        st.info(
            "Start date is considered as Credit Transfer approval date. "
            "Training will begin after credit transfer units."
        )

    if st.button("Generate Schedule"):

        schedule = generate_schedule(
            start_date,
            qualification_code,
            state,
            gap_option,
            credit_transfer_units
        )

        last_date = pd.to_datetime(schedule["End Date"]).max()
        contract_end = pd.to_datetime(contract_end_date)

        if last_date > contract_end:
            st.warning(
                "⚠️ Generated schedule exceeds Training Contract End Date. "
                "Please adjust start date or gap."
            )

        schedule_display = schedule.copy()

        schedule_display["Start Date"] = pd.to_datetime(
            schedule_display["Start Date"]
        ).dt.strftime("%d/%m/%Y")

        schedule_display["End Date"] = pd.to_datetime(
            schedule_display["End Date"]
        ).dt.strftime("%d/%m/%Y")

        st.dataframe(schedule_display, use_container_width=True)

        pdf_file = generate_pdf(
            schedule,
            learner_name,
            qualification_selected
        )

        file_name = f"{learner_name.strip().replace(' ', '_')}_schedule.pdf"

        st.download_button(
            "Download PDF",
            pdf_file,
            file_name=file_name
        )


# -------------------------
# MAIN
# -------------------------

if not st.session_state.logged_in:
    login()

else:

    menu = ["Scheduler"]

    if st.session_state.role == "admin":
        menu.append("Admin Panel")

    menu.append("Logout")

    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Scheduler":
        scheduler_ui()

    elif choice == "Admin Panel":
        admin_panel()

    elif choice == "Logout":
        st.session_state.logged_in = False
        st.rerun()
