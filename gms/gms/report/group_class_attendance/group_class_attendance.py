import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    if not data:
        return [], []
    return columns, data

def get_data(filters):
    conditions = []
    user = frappe.session.user

    if user != "Administrator":
        user_roles = frappe.get_doc("User", user)
        if 'Trainer' not in [role.role for role in user_roles.roles] and 'Member' not in [role.role for role in user_roles.roles]:
            return None

        if 'Member' in [role.role for role in user_roles.roles]:
            doc = frappe.get_doc("Gym Member", {"email": user})
            if 'member_name' not in filters:
                filters['member_name'] = []
            if isinstance(filters['member_name'], str):
                filters['member_name'] = [filters['member_name']]
            filters['member_name'].append(doc.full_name)

    if filters.get("meeting_id"):
        conditions.append(f"CA.name = '{filters['meeting_id']}'")

    if filters.get("member_name"):
        member_names = ', '.join(f"'{name}'" for name in filters['member_name'])
        conditions.append(f"M.full_name IN ({member_names})")

    if filters.get("location"):
        conditions.append(f"A.location LIKE '%{filters['location']}%'")

    if filters.get("attendance_status"):
        conditions.append(f"CA.presence = '{filters['attendance_status']}'")

    if filters.get("from_date"):
        conditions.append(f"A.meeting_date >= '{filters['from_date']}'")

    if filters.get("to_date"):
        conditions.append(f"A.meeting_date <= '{filters['to_date']}'")

    SQL_query = f"""
        SELECT
            CA.member AS member_id,
            M.full_name AS member_name,
            A.name AS meeting_id,
            CA.presence AS attendance_status,
            CA.time_in AS time_in,
            CA.time_out AS time_out,
            A.location AS location,
            A.date AS meeting_date,
            A.total_attendance AS total_attendance
        FROM
            `tabClass Attendance` AS CA
        JOIN
            `tabGym Member` AS M ON CA.member = M.name
        JOIN
            `tabAttendance` AS A ON CA.parent = A.name
        {'WHERE ' + ' AND '.join(conditions) if conditions else ''}
        ORDER BY
            A.date DESC
    """

    data = frappe.db.sql(SQL_query, as_dict=True)
    return data

def get_columns():
    return [
        {"fieldname": "meeting_id", "label": "Group Workout ID", "fieldtype": "Data", "width": 150, "align": "left"},
        {"fieldname": "member_name", "label": "Member Name", "fieldtype": "Data", "width": 150, "align": "left"},
        {"fieldname": "attendance_status", "label": "Attendance Status", "fieldtype": "Data", "width": 150, "align": "left"},
        {"fieldname": "time_in", "label": "Time In", "fieldtype": "Time", "width": 150, "align": "left"},
        {"fieldname": "time_out", "label": "Time Out", "fieldtype": "Time", "width": 150, "align": "left"},
        {"fieldname": "location", "label": "Location", "fieldtype": "Data", "width": 150, "align": "left"},
        {"fieldname": "meeting_date", "label": "Workout Date", "fieldtype": "Date", "width": 130, "align": "left"},
        {"fieldname": "total_attendance", "label": "Tot Attendance", "fieldtype": "Int", "width": 75, "align": "left"},
    ]
