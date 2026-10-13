frappe.ui.form.on("Batch", {
	refresh(frm) {
		if (frm.doc.custom_recalled) {
			frm.dashboard.add_comment(
				__("RECALLED - this batch is blocked from picking, delivery and invoicing."),
				"red",
				true
			);
		}
		if (!frm.is_new()) {
			frm.add_custom_button(
				__("Recall Traceability"),
				() => frappe.set_route("query-report", "Batch Recall Traceability", { batch_no: frm.doc.name }),
				__("View")
			);
		}
	},
});
