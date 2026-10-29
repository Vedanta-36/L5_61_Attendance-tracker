"""Attendance tracker: marks attendance, applies the 75% rule and exports."""
import csv
import glob
import os
import ssl
import tarfile
from datetime import datetime

import requests

# Global attendance register
students = {}

ERP_URL = "https://erp.college.example/api/attendance"
ERP_TIMEOUT_SECONDS = 10
MIN_ATTENDANCE = 75


def add_student(roll_no, name, section="A"):
    """Register a student with an empty attendance record."""
    students[roll_no] = {"name": name, "section": section, "records": []}


def mark_attendance(roll_no, date, status, register=None):
    """Record one attendance entry and return the per-date register."""
    if register is None:
        register = {}
    register.setdefault(date, []).append(roll_no)
    students[roll_no]["records"].append((date, status))
    return register


def attendance_percentage(roll_no):
    """Return the percentage of days the student was present (P)."""
    records = students[roll_no]["records"]
    total = len(records)
    if total == 0:
        return 0
    present = len([r for r in records if r[1] == "P"])
    return round(present / total * 100, 2)


def is_eligible(percentage):
    """Exam eligibility: at least MIN_ATTENDANCE percent."""
    return percentage >= MIN_ATTENDANCE


def shortage_list():
    """Return roll numbers of students below the eligibility threshold."""
    return [roll_no for roll_no in students
            if not is_eligible(attendance_percentage(roll_no))]


def has_long_absence(roll_no, days=3):
    """True if the student has `days` consecutive absences (A)."""
    statuses = [status for (_, status) in students[roll_no]["records"]]
    return any(statuses[i:i + days] == ["A"] * days
               for i in range(len(statuses)))


def latest_date(roll_no):
    """Return the most recent attendance date, compared as real dates."""
    dates = [r[0] for r in students[roll_no]["records"]]
    return max(dates, key=lambda d: datetime.strptime(d, "%Y-%m-%d"))


def _safe_cell(value):
    """Neutralise spreadsheet formulas (CSV injection) in text cells."""
    text = str(value)
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def export_csv(path="attendance.csv"):
    """Write name and percentage for every student to a CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["roll_no", "name", "percentage"])
        for roll_no, info in students.items():
            writer.writerow([_safe_cell(roll_no),
                             _safe_cell(info["name"]),
                             attendance_percentage(roll_no)])
    return path


def sync_to_erp(roll_no):
    """Send a student's percentage to the ERP; the key comes from the env."""
    payload = {"roll_no": roll_no, "pct": attendance_percentage(roll_no)}
    headers = {"X-API-Key": os.environ["ERP_API_KEY"]}
    response = requests.post(ERP_URL, json=payload, headers=headers,
                             timeout=ERP_TIMEOUT_SECONDS)
    return response.status_code


def backup_reports(archive="reports_backup.tgz"):
    """Archive all CSV reports without invoking a shell."""
    with tarfile.open(archive, "w:gz") as tar:
        for path in glob.glob("*.csv"):
            tar.add(path)
    return archive


def secure_channel():
    """Return a TLS context that refuses protocols older than TLS 1.2."""
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def run_job(command):
    """Describe a job; `command` is an argument list, never a shell string."""
    return {"command": command}


def schedule_reminders():
    """Schedule SMS reminders for students with an attendance shortage."""
    return run_job(["send_sms", "--shortage"])


def main():
    """Run a short demo of the tracker."""
    add_student("R01", "Aditi")
    add_student("R02", "=HYPERLINK(\"http://evil.example\",\"Bharat\")")
    register = {}
    for date, status in [("2026-09-01", "P"), ("2026-09-02", "P"),
                         ("2026-09-03", "L"), ("2026-09-04", "P"),
                         ("2026-09-05", "H")]:
        mark_attendance("R01", date, status, register)
    for date, status in [("2026-09-01", "P"), ("2026-09-01", "P"),
                         ("2026-09-02", "A"), ("2026-09-03", "A"),
                         ("2026-09-04", "A"), ("2026-9-3", "P")]:
        mark_attendance("R02", date, status, register)
    register = mark_attendance("R01", "2030-01-01", "P", register)
    print("R01 attendance %:", attendance_percentage("R01"))
    print("R02 attendance %:", attendance_percentage("R02"))
    print("Is 75% eligible?", is_eligible(75))
    print("Shortage list:", shortage_list())
    print("R02 long absence?", has_long_absence("R02"))
    print("R02 latest date:", latest_date("R02"))
    print("Register entries for 2026-09-01:", register["2026-09-01"])
    print("Exported to:", export_csv())
    print("Reminder job:", schedule_reminders())
    print("ERP sync skipped (no network)")


if __name__ == "__main__":
    main()