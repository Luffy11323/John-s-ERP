frappe.query_reports["Backorder and Inbound Supply"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{ fieldname: "customer", label: __("Customer"), fieldtype: "Link", options: "Customer" },
		{ fieldname: "item_code", label: __("Item"), fieldtype: "Link", options: "Item" },
		{ fieldname: "from_date", label: __("From Order Date"), fieldtype: "Date" },
		{ fieldname: "to_date", label: __("To Order Date"), fieldtype: "Date" },
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "shortfall" && data && data.shortfall > 0) {
			value = `<span style="color:#dc2626;font-weight:700">${value}</span>`;
		}
		return value;
	},
};
