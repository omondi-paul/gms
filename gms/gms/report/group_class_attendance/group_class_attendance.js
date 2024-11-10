frappe.query_reports["Group Class Attendance"] = {
	"filters": [
		{
			fieldname: "meeting_id",
			label: __("Meeting ID"),
			fieldtype: "Link",
			options: "Meeting",
			width: 150,
			reqd: 0
		},
		{
			fieldname: "member_name",
			label: __("Member Name"),
			fieldtype: "MultiSelectList",
			width: 150,
			reqd: 0,
			get_data: function(txt) {
				return frappe.db.get_link_options("Gym Member", txt);
			}
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
