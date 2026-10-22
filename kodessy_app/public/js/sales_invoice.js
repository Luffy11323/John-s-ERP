frappe.ui.form.on("Sales Invoice", {
	setup(frm) {
		toggle_return_columns(frm);
	},
	refresh(frm) {
		toggle_return_columns(frm);

		if (!frm.doc.is_return) return;

		if (frm.doc.custom_credit_note_approved_by) {
			frm.dashboard.add_comment(
				__("Credit note approved by {0}", [frm.doc.custom_credit_note_approved_by]),
				"green",
				true
			);
			return;
		}

		if (frm.doc.docstatus === 0 && !frm.is_new()) {
			frm.dashboard.add_comment(__("Pending Finance approval - cannot be submitted yet."), "orange", true);

			const approver_roles = ["Accounts Manager", "Finance Manager", "System Manager"];
			const can_approve = approver_roles.some(r => frappe.user.has_role(r));

			if (can_approve) {
				frm.add_custom_button(__("Approve Credit Note"), () => {
					frappe.call({
						method: "kodessy_app.controllers.credit_note_control.approve_credit_note",
						args: { name: frm.doc.name },
						freeze: true,
						callback: () => frm.reload_doc(),
					});
				});
			}
		}
	},
	is_return(frm) {
		toggle_return_columns(frm);
	}
});

function toggle_return_columns(frm) {
	const is_ret = !!frm.doc.is_return;
	if (frm.fields_dict.items && frm.fields_dict.items.grid) {
		const grid = frm.fields_dict.items.grid;
		if (typeof grid.set_column_disp === "function") {
			grid.set_column_disp("custom_return_reason", is_ret);
			grid.set_column_disp("custom_assessment_status", is_ret);
		}
	}
}
