frappe.ui.form.on("Gym Locker Booking", {
  refresh: function(frm) {
    if (frappe.session.user !== 'Administrator') {
      frm.set_df_property("end_date", "read_only", 1);
      frm.set_df_property("end_time", "read_only", 1);
      frm.set_df_property("start_date", "read_only", 1);
      frm.set_df_property("start_time", "read_only", 1);
    }
    if (frm.doc.workflow_state !== 'Draft') {
      frm.set_df_property("member", "read_only", 1);
      frm.set_df_property("locker_number", "read_only", 1);
      frm.set_df_property("booking_type", "read_only", 1);
      frm.set_df_property("start_date", "read_only", 1);
      frm.set_df_property("start_time", "read_only", 1);
    }
  },
  booking_type: function(frm) {
    if (frm.doc.booking_type == "Hours") {
      frm.set_value("number_of_days", "");
      frm.set_value("end_date", "");
      frm.set_value("start_date", "");
      frm.set_value("start_time", frappe.datetime.now_datetime());
    }
    if (frm.doc.booking_type == "Days") {
      frm.set_value("number_of_hours", "");
      frm.set_value("end_time", "");
      frm.set_value("end_time", "");
      frm.set_value("start_date", frappe.datetime.now_date());
    }
  },
  validate: function(frm) {
    fill_time(frm);
  }
});

function fill_time(frm) {
  frappe.call({
    method: "gms.services.rest.fill_time",
    args: {
      "name": frm.doc.name
    },
    callback: function(r) {
      let data = r.message;
      if (data.hours) {
        frm.set_value("number_of_hours", data.hours);
      } else if (data.days) {
        frm.set_value("number_of_days", data.days);
      }
    }
  });
}
