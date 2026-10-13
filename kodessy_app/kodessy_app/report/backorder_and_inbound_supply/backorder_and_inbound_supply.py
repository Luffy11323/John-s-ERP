import frappe
from frappe import _
from frappe.utils import flt

CLOSED_SO = ("Closed", "Completed", "Cancelled", "On Hold", "Draft")
CLOSED_PO = ("Closed", "Completed", "Cancelled", "On Hold", "Draft", "Delivered")


def execute(filters=None):
	filters = frappe._dict(filters or {})
	data = _get_data(filters)
	return _columns(), data


def _columns():
	return [
		{"label": _("Sales Order"), "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 140},
		{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 160},
		{"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 190},
		{"label": _("Ordered"), "fieldname": "ordered", "fieldtype": "Float", "width": 80},
		{"label": _("Delivered"), "fieldname": "delivered", "fieldtype": "Float", "width": 80},
		{"label": _("Backorder Qty"), "fieldname": "backorder", "fieldtype": "Float", "width": 100},
		{"label": _("Promised Delivery"), "fieldname": "delivery_date", "fieldtype": "Date", "width": 110},
		{"label": _("Stock On Hand"), "fieldname": "on_hand", "fieldtype": "Float", "width": 100},
		{"label": _("Shortfall vs Stock"), "fieldname": "shortfall", "fieldtype": "Float", "width": 110},
		{"label": _("Inbound PO Qty"), "fieldname": "inbound_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Expected Arrival"), "fieldname": "expected_arrival", "fieldtype": "Date", "width": 110},
		{"label": _("Inbound PO(s)"), "fieldname": "inbound_pos", "fieldtype": "Data", "width": 200},
	]


def _get_data(filters):
	conditions, values = [], {}
	if filters.get("company"):
		conditions.append("so.company = %(company)s")
		values["company"] = filters.company
	if filters.get("customer"):
		conditions.append("so.customer = %(customer)s")
		values["customer"] = filters.customer
	if filters.get("from_date"):
		conditions.append("so.transaction_date >= %(from_date)s")
		values["from_date"] = filters.from_date
	if filters.get("to_date"):
		conditions.append("so.transaction_date <= %(to_date)s")
		values["to_date"] = filters.to_date
	if filters.get("item_code"):
		conditions.append("soi.item_code = %(item_code)s")
		values["item_code"] = filters.item_code

	where = (" AND " + " AND ".join(conditions)) if conditions else ""
	lines = frappe.db.sql(
		f"""
		SELECT so.name AS sales_order, so.customer, soi.item_code, soi.item_name,
		       soi.qty AS ordered, soi.delivered_qty AS delivered,
		       COALESCE(soi.delivery_date, so.delivery_date) AS delivery_date
		FROM `tabSales Order Item` soi
		JOIN `tabSales Order` so ON so.name = soi.parent
		WHERE so.docstatus = 1 AND so.status NOT IN %(closed)s
		  AND soi.qty > soi.delivered_qty {where}
		ORDER BY delivery_date, so.name
		""",
		{**values, "closed": CLOSED_SO},
		as_dict=True,
	)
	if not lines:
		return []

	items = list({l.item_code for l in lines})
	on_hand = {
		r.item_code: flt(r.qty)
		for r in frappe.db.sql(
			"SELECT item_code, SUM(actual_qty) qty FROM `tabBin` WHERE item_code IN %(items)s GROUP BY item_code",
			{"items": items},
			as_dict=True,
		)
	}

	inbound = {}
	for r in frappe.db.sql(
		"""
		SELECT poi.item_code, po.name AS po, poi.schedule_date,
		       (poi.qty - poi.received_qty) AS pending
		FROM `tabPurchase Order Item` poi
		JOIN `tabPurchase Order` po ON po.name = poi.parent
		WHERE po.docstatus = 1 AND po.status NOT IN %(closed)s
		  AND poi.qty > poi.received_qty AND poi.item_code IN %(items)s
		ORDER BY poi.schedule_date
		""",
		{"items": items, "closed": CLOSED_PO},
		as_dict=True,
	):
		inbound.setdefault(r.item_code, []).append(r)

	# Allocate stock on hand to the oldest promised orders first; the rest is shortfall.
	remaining_stock = dict(on_hand)
	data = []
	for l in lines:
		backorder = flt(l.ordered) - flt(l.delivered)
		available = max(flt(remaining_stock.get(l.item_code)), 0)
		covered = min(available, backorder)
		remaining_stock[l.item_code] = available - covered

		pos = inbound.get(l.item_code, [])
		data.append(
			{
				**l,
				"backorder": backorder,
				"on_hand": on_hand.get(l.item_code, 0),
				"shortfall": backorder - covered,
				"inbound_qty": sum(flt(p.pending) for p in pos),
				"expected_arrival": pos[0].schedule_date if pos else None,
				"inbound_pos": ", ".join(dict.fromkeys(p.po for p in pos)),
			}
		)
	return data
