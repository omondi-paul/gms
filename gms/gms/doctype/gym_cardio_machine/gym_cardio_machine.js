frappe.ui.form.on("Gym Cardio Machine", {
  refresh(frm) {
    frm.set_df_property("tab_2_tab", "hidden", 1);

    if (!frm.doc.__islocal && frm.doc.docstatus == 0) {
      frm.add_custom_button(__('Book'), function () {
        let machine = frm.doc.name;
        let machine_location = frm.doc.location;
        let machine_type = frm.doc.machine_type;

        frappe.ui.form.on('Cardio Machine Booking', {
          setup: function(frm) {
            frm.set_value('cardio_machine', machine);
            frm.set_value('machine_location', machine_location);
            frm.set_value('machine_type', machine_type);
          }
        });
        frappe.set_route('form', 'Cardio Machine Booking', 'new-cardio-machine-booking-mkkgspdezc');
      }).addClass('btn-primary');
    }
  },
});
