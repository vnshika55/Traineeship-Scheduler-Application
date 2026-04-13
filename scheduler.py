import pandas as pd
from datetime import timedelta
from dateutil.relativedelta import relativedelta

# PDF Libraries
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from io import BytesIO


# -----------------------------
# LOAD QUALIFICATIONS
# -----------------------------
def load_qualifications():
    df = pd.read_csv("data/qualifications.csv", encoding="latin1")
    df.columns = df.columns.str.strip().str.lower()
    return df


# -----------------------------
# LOAD UNITS
# -----------------------------
def load_units(qualification_code):

    df = pd.read_csv("data/Units.csv", encoding="latin1")

    df.columns = df.columns.str.strip().str.lower()
    df["qualification_code"] = df["qualification_code"].astype(str).str.strip()

    qualification_code = str(qualification_code).strip()

    units = df[df["qualification_code"] == qualification_code]
    units = units.sort_values("sequence")

    return units.reset_index(drop=True)


# -----------------------------
# LOAD PUBLIC HOLIDAYS
# -----------------------------
def load_holidays(state):

    df = pd.read_csv("data/public_holidays.csv", encoding="latin1")

    df.columns = df.columns.str.strip().str.lower()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["state"] = df["state"].astype(str).str.strip()

    holidays = df[df["state"] == state]["date"]

    return set(holidays.dropna())


# -----------------------------
# SKIP WEEKENDS + HOLIDAYS
# -----------------------------
def get_next_valid_day(date, holidays):

    while date.weekday() >= 5 or date in holidays:
        date += timedelta(days=1)

    return date


# -----------------------------
# CALCULATE END DATE
# -----------------------------
def calculate_end_date(start_date, gap_option, holidays):

    if gap_option == "month":
        end_date = start_date + relativedelta(months=1)

    elif gap_option == "2weeks":
        end_date = start_date + timedelta(weeks=2)

    elif gap_option == "3weeks":
        end_date = start_date + timedelta(weeks=3)

    elif gap_option == "4weeks":
        end_date = start_date + timedelta(weeks=4)

    else:
        end_date = start_date + relativedelta(months=1)

    end_date = get_next_valid_day(end_date, holidays)

    return end_date


# -----------------------------
# GENERATE SCHEDULE
# -----------------------------
def generate_schedule(start_date, qualification_code, state,
                      gap_option="month", credit_transfer_units=None):

    if credit_transfer_units is None:
        credit_transfer_units = []

    start_date = pd.to_datetime(start_date).date()

    units_df = load_units(qualification_code)
    holidays = load_holidays(state)

    schedule = []

    # -----------------------------
    # CREDIT TRANSFER UNITS
    # -----------------------------
    for _, row in units_df.iterrows():

        if row["unit_code"] in credit_transfer_units:
            schedule.append({
                "Start Date": start_date,
                "Unit Code": row["unit_code"],
                "Unit Name": row["unit_name"],
                "End Date": start_date,
                "Type": "Credit Transfer"
            })

    # -----------------------------
    # START DATE LOGIC
    # -----------------------------
    if credit_transfer_units:
        # start next day only if CT exists
        current_start = start_date + timedelta(days=1)
    else:
        # start same day if no CT
        current_start = start_date

    current_start = get_next_valid_day(current_start, holidays)

    # -----------------------------
    # TRAINING UNITS
    # -----------------------------
    for _, row in units_df.iterrows():

        if row["unit_code"] in credit_transfer_units:
            continue

        current_start = get_next_valid_day(current_start, holidays)

        end_date = calculate_end_date(current_start, gap_option, holidays)

        schedule.append({
            "Start Date": current_start,
            "Unit Code": row["unit_code"],
            "Unit Name": row["unit_name"],
            "End Date": end_date,
            "Type": "Training"
        })

        current_start = end_date + timedelta(days=1)

    schedule_df = pd.DataFrame(schedule)

    schedule_df = schedule_df.sort_values(
        by=["Type", "Start Date"],
        ascending=[True, True]
    )

    return schedule_df.reset_index(drop=True)


# -----------------------------
# GENERATE PDF
# -----------------------------
def generate_pdf(schedule_df, learner_name, qualification):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4)
    )

    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph("Traineeship Class Schedule", styles["Title"])
    elements.append(title)

    elements.append(Spacer(1, 20))

    learner = Paragraph(f"<b>Learner Name:</b> {learner_name}", styles["Normal"])
    qual = Paragraph(f"<b>Qualification:</b> {qualification}", styles["Normal"])

    elements.append(learner)
    elements.append(qual)

    elements.append(Spacer(1, 20))

    df = schedule_df.copy()

    df["Start Date"] = pd.to_datetime(df["Start Date"]).dt.strftime("%d/%m/%Y")
    df["End Date"] = pd.to_datetime(df["End Date"]).dt.strftime("%d/%m/%Y")

    data = [df.columns.tolist()] + df.values.tolist()

    table = Table(
        data,
        repeatRows=1,
        colWidths=[90, 120, 420, 90, 120]
    )

    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]

    for i, row in df.iterrows():
        if row["Type"] == "Credit Transfer":
            style.append(
                ("BACKGROUND", (0, i + 1), (-1, i + 1), colors.HexColor("#FFF3CD"))
            )
            style.append(
                ("FONTNAME", (0, i + 1), (-1, i + 1), "Helvetica-Bold")
            )

    table.setStyle(TableStyle(style))

    elements.append(table)

    elements.append(Spacer(1, 40))

    signature_table = Table([
        ["Trainer Signature", "Learner Signature", "Date"],
        ["", "", ""]
    ], colWidths=[200, 200, 200])

    signature_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER")
    ]))

    elements.append(signature_table)

    doc.build(elements)

    buffer.seek(0)

    return buffer
