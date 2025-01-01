frappe.ui.form.on("Attendance", {
	group_class(frm) {
		frappe.call({
			method: "gms.services.rest.fetch_class_attendees",
			args: {
				"group_class": frm.doc.group_class
			},
			callback: function(r) {
				if (r.message) {
					frm.set_value("attendees", r.message);
					console.log("attendees are", r.message);
				} else {
					frappe.msgprint(__("Member not found for the current user email."));
				}
			}
		});
	},
	validate(frm) {
		frappe.call({
			method: "gms.services.rest.get_total_attendance",
			args: {
				"name": frm.doc.name
			},
			callback: function(r) {
				
			}
		});
	},
	onload: function (frm) {
    if (frm.doc.group_class) {
        frappe.call({
            method: "gms.services.rest.get_group_class_members",
            args: {
                "group_class": frm.doc.group_class
            },
            callback: function (r) {
                if (r.message) {
                    frm.fields_dict['attendees'].grid.get_field('member').get_query = function (doc, cdt, cdn) {
                        return {
                            filters: [
                                ['Gym Member', 'name', 'in', r.message]
                            ]
                        };
                    };
                } else {
                    frappe.msgprint(__('No members found for the selected group class.'));
                }
            }
        });
    }
}


});


frappe.ui.form.on("Class Attendance", {
	presence(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.presence !== "Present") {
			frappe.model.set_value(cdt, cdn, {
				"time_in": "",
				"time_out": ""
			});
		}
	}
});
