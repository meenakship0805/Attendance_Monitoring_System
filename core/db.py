"""
core/db.py — Student & attendance persistence.

Kept as Excel/pandas exactly like the original desktop app — it already
works and doesn't need to change for the Streamlit port. Only the Tkinter
calls that used to sit next to these functions have been removed.

Note: Streamlit Cloud's filesystem is ephemeral (resets on redeploy/sleep),
so student_data.xlsx / attendance_records.xlsx won't survive a redeploy.
That's fine for a resume demo — mention it as a known limitation if asked,
or swap this file for a Supabase/SQLite backend later without touching
any other file (that's the point of keeping this isolated).
"""

import os
import pandas as pd
from datetime import datetime, date

STUDENT_FILE = "student_data.xlsx"
ATTENDANCE_FILE = "attendance_records.xlsx"


def add_student_to_excel(student_id, name, age, gender):
    row = pd.DataFrame({
        "student_id": [int(student_id)],
        "student_name": [name],
        "age": [int(age) if age else ""],
        "gender": [gender]
    })
    if not os.path.exists(STUDENT_FILE):
        row.to_excel(STUDENT_FILE, index=False)
        return True, "Student added successfully."
    df = pd.read_excel(STUDENT_FILE)
    if int(student_id) in df["student_id"].values:
        return False, f"Student ID {student_id} already exists."
    pd.concat([df, row], ignore_index=True).to_excel(STUDENT_FILE, index=False)
    return True, "Student added successfully."


def get_all_students():
    if os.path.exists(STUDENT_FILE):
        return pd.read_excel(STUDENT_FILE)
    return pd.DataFrame(columns=["student_id", "student_name", "age", "gender"])


def get_student_name(student_id):
    df = get_all_students()
    row = df[df["student_id"] == student_id]
    return row["student_name"].values[0] if not row.empty else "Unknown"


def mark_attendance(student_id, student_name):
    now = datetime.now()
    today = date.today().isoformat()
    if os.path.exists(ATTENDANCE_FILE):
        df = pd.read_excel(ATTENDANCE_FILE)
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date.astype(str)
        if not df[(df["student_id"] == student_id) & (df["date"] == today)].empty:
            return False
    row = pd.DataFrame({
        "student_id": [student_id],
        "student_name": [student_name],
        "timestamp": [now.strftime("%Y-%m-%d %H:%M:%S")]
    })
    if not os.path.exists(ATTENDANCE_FILE):
        row.to_excel(ATTENDANCE_FILE, index=False)
    else:
        df_existing = pd.read_excel(ATTENDANCE_FILE)
        pd.concat([df_existing, row], ignore_index=True).to_excel(ATTENDANCE_FILE, index=False)
    return True


def get_attendance_records(filter_date=None):
    if not os.path.exists(ATTENDANCE_FILE):
        return pd.DataFrame(columns=["student_id", "student_name", "timestamp"])
    df = pd.read_excel(ATTENDANCE_FILE)
    if filter_date:
        df["_date"] = pd.to_datetime(df["timestamp"]).dt.date.astype(str)
        df = df[df["_date"] == filter_date].drop(columns=["_date"])
    return df
