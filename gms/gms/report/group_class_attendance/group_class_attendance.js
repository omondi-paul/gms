frappe.query_reports["Group Class Attendance"] = {
	"filters": [
		{
			fieldname: "group_class",
			label: __("Workout Name"),
			fieldtype: "Link",
			options: "Group Class",
			width: 150,
			reqd: 0
		},
		{
			fieldname: "member_id",
			label: __("Member ID"),
			fieldtype: "Link",
			width: 150,
			reqd: 0,
			options: "Gym Member",
		},
		{
			fieldname: "location",
			label: __("Location"),
			fieldtype: "Link",
			options: "Gym Location",
			width: 150,
			reqd: 0
		},
		{
			fieldname: "attendance_status",
			label: __("Attendance Status"),
			fieldtype: "Select",
			options: [
				{ "value": "", "label": __("All") },
				{ "value": "Present", "label": __("Present") },
				{ "value": "Absent", "label": __("Absent") },
				{ "value": "Late", "label": __("Late") },
				{ "value": "Excused", "label": __("Excused") }
			],
			width: 150,
			reqd: 0
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			width: 80,
			reqd: 0
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			width: 80,
			reqd: 0
		}
	]
};
