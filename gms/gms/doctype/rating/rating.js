// Copyright (c) 2025, Polito and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rating", {
  refresh: function(frm) {
    if (frappe.session.user != 'Administrator') {
    frm.set_df_property("gym_member", "read_only", 1);

    frappe.call({
      method: "frappe.client.get",
      args: {
        doctype: "Gym Member",
        filters: {"email": frappe.session.user}
      },
      callback: function(r) {
        if (r.message) {
          let member = r.message;
          frm.set_value("gym_member", member.name);
        } else {
          frappe.msgprint(__("Member not found for the current user email."));
        }
      }
    });
  }


  },

});
