frappe.ui.form.on("Contact", {
	onload(frm) {
		if (frm.is_new()) {
			if (!frm.doc.is_primary_contact) {
				frm.set_value("is_primary_contact", 1);
			}
			if (!frm.doc.is_billing_contact) {
				frm.set_value("is_billing_contact", 1);
			}
		}
	},
	refresh(frm) {
		if (frm.is_new()) {
			if (!frm.doc.is_primary_contact) {
				frm.set_value("is_primary_contact", 1);
			}
			if (!frm.doc.is_billing_contact) {
				frm.set_value("is_billing_contact", 1);
			}
		}
	}
});
