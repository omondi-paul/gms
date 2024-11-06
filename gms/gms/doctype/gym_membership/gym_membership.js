frappe.ui.form.on("Gym Membership", {
  refresh: function(frm) {
    if (frappe.session.user !== 'Administrator') {

      frm.set_df_property("member",  "read_only", 1);
      frm.set_df_property("date_of_subscription", "read_only", 1);
      frm.set_value("date_of_subscription", frappe.datetime.now_date());
      frappe.call({
        method: "frappe.client.get",
        args: {
          doctype: "Gym Member",
          filters: {"email": frappe.session.user}
        },
        callback: function(r) {
          if (r.message) {
            let member = r.message;
            frm.set_value("member", member.name);
          } else {
            frappe.msgprint(__("Member not found for the current user email."));
          }
        }
      });
    }

  },
 
});

