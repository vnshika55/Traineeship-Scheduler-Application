import streamlit as st
import pandas as pd
from io import StringIO

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

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None


# LOGIN
def login():

    st.title("Traineeship Scheduler Login")

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


# ADMIN PANEL
def admin_panel():

    st.title("Admin Panel")

    col1, col2, col3 = st.columns(3)

    email = col1.text_input("Email").strip().lower()
    password = col2.text_input("Password")
    role = col3.selectbox("Role", ["user", "admin"])

    if st.button("Add User"):

        success = add_user(email, password, role)

        if success:
            st.success("User Added")
            st.rerun()
        else:
            st.error("User already exists")

    st.divider()

    users = get_users()

    for user in users:

        col1, col2, col3, col4, col5 = st.columns([3,1,1,1,1])

        col1.write(user[1])
        col2.write(user[3])
        col3.write("Active" if user[4] else "Disabled")

        if col4.button("Toggle", key=f"toggle{user[0]}"):
            toggle_user(user[0])
            st.rerun()

        if col5.button("Delete", key=f"delete{user[0]}"):
            delete_user(user[0])
            st.rerun()


# SCHEDULER
def scheduler_ui():

    st.title("Traineeship Scheduler")

    qual_df = load_qualifications()

    qualification_display = {
        f"{row['qualification_code']} - {row['qualification_name']}":
        row['qualification_code']
        for _, row in qual_df.iterrows()
    }

    learner_name = st.text_input("Learner Name")
    state = st.selectbox("State", ["NSW", "ACT"])
    qualification_selected = st.selectbox("Qualification", list(qualification_display.keys()))

    gap_option = st.selectbox(
        "Gap Between Units",
        ["2weeks", "3weeks", "4weeks", "month"]
    )

    qualification_code = qualification_display[qualification_selected]

    start_date = st.date_input("Start Date")
    contract_end_date = st.date_input("Training Contract End Date")

    units_df = load_units(qualification_code)
    unit_codes = units_df["unit_code"].tolist()

    credit_transfer_units = st.multiselect(
        "Credit Transfer Units",
        unit_codes
    )

    if st.button("Generate Schedule"):

        schedule = generate_schedule(
            start_date,
            qualification_code,
            state,
            gap_option,
            credit_transfer_units
        )

        save_schedule(
            learner_name,
            qualification_selected,
            state,
            st.session_state.user,
            schedule
        )

        st.dataframe(schedule, use_container_width=True)

        st.download_button(
            "Download CSV",
            schedule.to_csv(index=False),
            file_name=f"{learner_name}_schedule.csv"
        )

        pdf = generate_pdf(schedule, learner_name, qualification_selected)

        st.download_button(
            "Download PDF",
            pdf,
            file_name=f"{learner_name}_schedule.pdf"
        )


# HISTORY
def schedule_history():

    st.title("Schedule History")

    schedules = get_schedules()

    for row in schedules:

        schedule_id = row[0]

        with st.expander(
            f"{row[1]} | {row[2]} | {row[4]} | {row[5]}"
        ):

            csv_data = get_schedule(schedule_id)

            df = pd.read_csv(StringIO(csv_data))

            st.dataframe(df, use_container_width=True)

            col1, col2, col3 = st.columns(3)

            col1.download_button(
                "Download CSV",
                df.to_csv(index=False),
                file_name=f"{row[1]}_schedule.csv",
                key=f"csv{schedule_id}"
            )

            pdf = generate_pdf(df, row[1], row[2])

            col2.download_button(
                "Download PDF",
                pdf,
                file_name=f"{row[1]}_schedule.pdf",
                key=f"pdf{schedule_id}"
            )

            if st.session_state.role == "admin":
                if col3.button("Delete", key=f"delete{schedule_id}"):
                    delete_schedule(schedule_id)
                    st.rerun()


# MAIN
if not st.session_state.logged_in:
    login()

else:

    menu = ["Scheduler", "Schedule History"]

    if st.session_state.role == "admin":
        menu.append("Admin Panel")

    menu.append("Logout")

    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Scheduler":
        scheduler_ui()

    elif choice == "Schedule History":
        schedule_history()

    elif choice == "Admin Panel":
        admin_panel()

    elif choice == "Logout":
        st.session_state.logged_in = False
        st.rerun()
