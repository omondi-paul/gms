frappe.ui.form.on("Gym Membership", {
  refresh: function(frm) {
    if (frappe.session.user !== 'Administrator') {
      frm.set_df_property("member",  "read_only", 1);
      frm.set_df_property("date_of_subscription", "read_only", 1);
    }

  },
 
});

