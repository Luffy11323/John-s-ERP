import frappe
from frappe import _
from frappe.utils import flt

SUPPLIER_DOCS = ("Purchase Receipt",)
CUSTOMER_DOCS = ("Delivery Note", "Sales Invoice")


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.batch_no:
		frappe.throw(_("Please select a Batch No"))

	batch = frappe.db.get_value(
		"Batch", filters.batch_no, ["item", "expiry_date", "disabled", "custom_recalled"], as_dict=True
	)
	if not batch:
		frappe.throw(_("Batch {0} not found").format(filters.batch_no))

	records = _collect(filters.batch_no)
	data = _resolve(records)
	data.sort(key=lambda r: (str(r.get("posting_date") or ""), r.get("document") or ""))

	received = sum(flt(r["qty"]) for r in data if r["stage"] == "Supplier Receipt")
	delivered = sum(flt(r["qty"]) for r in data if r["stage"] == "Customer Delivery")
	customers = {r["party"] for r in data if r["stage"] == "Customer Delivery" and r["party"]}

	message = _("Batch <b>{0}</b> &mdash; Item: {1} &mdash; Expiry: {2} &mdash; Status: {3}").format(
		filters.batch_no,
		batch.item,
		batch.expiry_date or _("n/a"),
		"<span style='color:#dc2626'><b>RECALLED</b></span>" if batch.custom_recalled else _("Active"),
	)
	summary = [
		{"value": received, "label": _("Received from Suppliers"), "datatype": "Float", "indicator": "Blue"},
		{"value": delivered, "label": _("Delivered to Customers"), "datatype": "Float", "indicator": "Orange"},
		{"value": len(customers), "label": _("Customers Affected"), "datatype": "Int", "indicator": "Red"},
	]
	return _columns(), data, message, None, summary


def _columns():
	return [
		{"label": _("Stage"), "fieldname": "stage", "fieldtype": "Data", "width": 130},
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": _("Document Type"), "fieldname": "doctype", "fieldtype": "Data", "width": 130},
		{"label": _("Document"), "fieldname": "document", "fieldtype": "Dynamic Link", "options": "doctype", "width": 170},
		{"label": _("Party"), "fieldname": "party", "fieldtype": "Data", "width": 190},
		{"label": _("Qty"), "fieldname": "qty", "fieldtype": "Float", "width": 90},
		{"label": _("Mobile"), "fieldname": "mobile_no", "fieldtype": "Data", "width": 120},
		{"label": _("Email"), "fieldname": "email_id", "fieldtype": "Data", "width": 180},
	]


def _collect(batch_no):
	"""Return {(doctype, name): qty} from Serial and Batch Bundles and legacy item-level batch_no."""
	records = {}

	bundle_rows = frappe.db.sql(
		"""
		SELECT sbb.voucher_type, sbb.voucher_no, SUM(ABS(sbe.qty)) AS qty
		FROM `tabSerial and Batch Entry` sbe
		JOIN `tabSerial and Batch Bundle` sbb ON sbb.name = sbe.parent
		WHERE sbe.batch_no = %s AND sbb.docstatus = 1 AND sbb.is_cancelled = 0
		  AND sbb.voucher_type IN ('Purchase Receipt', 'Delivery Note', 'Sales Invoice')
		GROUP BY sbb.voucher_type, sbb.voucher_no
		""",
		batch_no,
		as_dict=True,
	)
	for r in bundle_rows:
		records[(r.voucher_type, r.voucher_no)] = flt(r.qty)

	legacy = {
		"Purchase Receipt": "SELECT parent, SUM(qty) qty FROM `tabPurchase Receipt Item` WHERE batch_no=%s AND docstatus=1 GROUP BY parent",
		"Delivery Note": "SELECT parent, SUM(qty) qty FROM `tabDelivery Note Item` WHERE batch_no=%s AND docstatus=1 GROUP BY parent",
		"Sales Invoice": (
			"SELECT i.parent, SUM(i.qty) qty FROM `tabSales Invoice Item` i "
			"JOIN `tabSales Invoice` s ON s.name=i.parent "
			"WHERE i.batch_no=%s AND i.docstatus=1 AND s.update_stock=1 GROUP BY i.parent"
		),
	}
	for doctype, query in legacy.items():
		for r in frappe.db.sql(query, batch_no, as_dict=True):
			records.setdefault((doctype, r.parent), flt(r.qty))
	return records


def _resolve(records):
	rows = []
	for (doctype, name), qty in records.items():
		if doctype in SUPPLIER_DOCS:
			d = frappe.db.get_value(doctype, name, ["posting_date", "supplier", "supplier_name"], as_dict=True) or {}
			rows.append(
				{
					"stage": "Supplier Receipt",
					"posting_date": d.get("posting_date"),
					"doctype": doctype,
					"document": name,
					"party": d.get("supplier_name") or d.get("supplier"),
					"qty": qty,
				}
			)
		else:
			d = frappe.db.get_value(doctype, name, ["posting_date", "customer", "customer_name"], as_dict=True) or {}
			contact = (
				frappe.db.get_value("Customer", d.get("customer"), ["mobile_no", "email_id"], as_dict=True)
				if d.get("customer")
				else {}
			) or {}
			rows.append(
				{
					"stage": "Customer Delivery",
					"posting_date": d.get("posting_date"),
					"doctype": doctype,
					"document": name,
					"party": d.get("customer_name") or d.get("customer"),
					"qty": qty,
					"mobile_no": contact.get("mobile_no"),
					"email_id": contact.get("email_id"),
				}
			)
	return rows
