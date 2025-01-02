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
            if 'member_id' not in filters:
                filters['member_id'] = []
            if isinstance(filters['member_id'], str):
                filters['member_id'] = [filters['member_id']]
            filters['member_id'].append(doc.name)

    if filters.get("group_class"):
        conditions.append("A.group_class = %(group_class)s")


    if filters.get("member_id"):
        member_ids = ", ".join([frappe.db.escape(member) for member in filters['member_id']])
        conditions.append(f"CA.member IN ({member_ids})")

    if filters.get("location"):
        conditions.append("A.location LIKE %(location)s")

    if filters.get("attendance_status"):
        conditions.append("CA.presence = %(attendance_status)s")

    if filters.get("from_date"):
        conditions.append("A.date >= %(from_date)s")

    if filters.get("to_date"):
        conditions.append("A.date <= %(to_date)s")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    SQL_query = f"""
        SELECT
            CA.member AS member_id,
            M.full_name AS member_name,
            A.name AS meeting_id,
            A.group_class AS group_class,
            CA.presence AS attendance_status,
            CA.time_in AS time_in,
            CA.time_out AS time_out,
            A.location AS location,
            A.date AS meeting_date,
            A.total_attendance AS total_attendance
        FROM
            `tabClass Attendance` AS CA
        JOIN
            `tabGym Member` AS M ON CA.member = M.full_name
        JOIN
            `tabAttendance` AS A ON CA.parent = A.name
        {where_clause}
        ORDER BY
            A.date DESC
    """

    data = frappe.db.sql(SQL_query, filters, as_dict=True)

    print(f"\n\n\n {data}\n\n\n")
    return data


def get_columns():
    return [
        {"fieldname": "group_class", "label": "Workout Class", "fieldtype": "Data", "width": 150, "align": "left"},
        {"fieldname": "member_name", "label": "Member Name", "fieldtype": "Data", "width": 150, "align": "left"},
        {"fieldname": "attendance_status", "label": "Attendance Status", "fieldtype": "Data", "width": 150, "align": "left"},
        {"fieldname": "time_in", "label": "Time In", "fieldtype": "Time", "width": 150, "align": "left"},
        {"fieldname": "time_out", "label": "Time Out", "fieldtype": "Time", "width": 150, "align": "left"},
        {"fieldname": "location", "label": "Location", "fieldtype": "Data", "width": 150, "align": "left"},
        {"fieldname": "meeting_date", "label": "Workout Date", "fieldtype": "Date", "width": 130, "align": "left"},
        {"fieldname": "total_attendance", "label": "Tot Attendance", "fieldtype": "Int", "width": 75, "align": "left"},
    ]
