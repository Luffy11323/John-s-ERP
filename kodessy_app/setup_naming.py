import frappe

# DocType -> prefix. Result format: PREFIX-YYYY-####  (e.g. QTR-2026-0001)
NAMING_PREFIXES = {
	"Quotation": "QTR",
	"Sales Order": "SO",
	"Delivery Note": "DO",
	"Sales Invoice": "SINV",
	"Pick List": "PCK",
	"Material Request": "MR",
	"Purchase Order": "PUR",
	"Purchase Receipt": "GRN",
	"Purchase Invoice": "PINV",
	"Stock Entry": "STE",
	"Stock Reconciliation": "SRC",
	"Quality Inspection": "QI",
	"Payment Entry": "PAY",
	"Journal Entry": "JV",
	"Supplier Quotation": "SQ",
	"Request for Quotation": "RFQ",
}


def series_for(prefix):
	return f"{prefix}-.YYYY.-.####"


def apply_naming_series():
	"""Idempotent. Sets naming_series options/default on every document in NAMING_PREFIXES."""
	for doctype, prefix in NAMING_PREFIXES.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		meta = frappe.get_meta(doctype)
		if not meta.has_field("naming_series"):
			continue
		series = series_for(prefix)
		frappe.make_property_setter(
			{
				"doctype": doctype,
				"doctype_or_field": "DocField",
				"fieldname": "naming_series",
				"property": "options",
				"value": series,
				"property_type": "Text",
			},
			validate_fields_for_doctype=False,
		)
		frappe.make_property_setter(
			{
				"doctype": doctype,
				"doctype_or_field": "DocField",
				"fieldname": "naming_series",
				"property": "default",
				"value": series,
				"property_type": "Text",
			},
			validate_fields_for_doctype=False,
		)
		frappe.clear_cache(doctype=doctype)
	frappe.db.commit()


def after_migrate():
	apply_naming_series()
