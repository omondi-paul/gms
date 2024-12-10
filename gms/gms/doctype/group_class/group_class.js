frappe.ui.form.on("Group Class", {
  refresh(frm) {
      if (!frm.doc.__islocal) {
          frm.add_custom_button(__('Join Class'), function () {
              let group_class = frm.doc.name;

              frappe.ui.form.on('Join Class', {
                  setup: function(frm) {
                      frm.set_value('group_class', group_class);
                  }
              });
              frappe.set_route('form', 'Join Class', 'new-join-class-1');
          }).addClass('btn-primary');
      }
  },
});
