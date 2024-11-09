// Copyright (c) 2024, Polito and contributors
// For license information, please see license.txt

frappe.ui.form.on("Attendance", {
	group_class(frm) {
    frappe.call({
      method: "gms.services.rest.fetch_class_attendees",
      args: {
       "group_class":frm.doc.group_class
      },
      callback: function(r) {
        if (r.message) {
          frm.set_value("attendees",r.message)
          console.log("attendees are",r.message)
        } else {
          frappe.msgprint(__("Member not found for the current user email."));
        }
      }
    });

	},
});
