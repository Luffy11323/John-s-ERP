frappe.query_reports["Batch Recall Traceability"] = {
	filters: [
		{
			fieldname: "batch_no",
			label: __("Batch No"),
			fieldtype: "Link",
			options: "Batch",
			reqd: 1,
		},
	],
};
