# -*- coding: utf-8 -*-
import frappe
from frappe import _


@frappe.whitelist()
def get_auto_batch(item_code, warehouse=None):
	"""Return the earliest unexpired batch for an item (FEFO), with warehouse priority."""
	if not item_code:
		return None

	has_batch = frappe.db.get_value("Item", item_code, "has_batch_no")
	if not has_batch:
		return None

	# 1. Search Frappe v15 Serial and Batch Entry with available stock in warehouse
	if warehouse:
		batches = frappe.db.sql("""
			SELECT b.name
			FROM `tabBatch` b
			JOIN `tabSerial and Batch Entry` sbe ON sbe.batch_no = b.name
			WHERE b.item = %s
			  AND b.disabled = 0
			  AND (b.custom_recalled = 0 OR b.custom_recalled IS NULL)
			  AND (b.expiry_date >= CURDATE() OR b.expiry_date IS NULL)
			  AND sbe.warehouse = %s
			  AND sbe.docstatus = 1
			GROUP BY b.name
			HAVING SUM(sbe.qty) > 0
			ORDER BY b.expiry_date ASC
			LIMIT 1
		""", (item_code, warehouse), as_dict=True)
		if batches:
			return batches[0].name

		# 2. Search legacy Stock Ledger Entry with available stock in warehouse
		batches = frappe.db.sql("""
			SELECT b.name
			FROM `tabBatch` b
			JOIN `tabStock Ledger Entry` sle ON sle.batch_no = b.name
			WHERE b.item = %s 
			  AND b.disabled = 0
			  AND (b.custom_recalled = 0 OR b.custom_recalled IS NULL)
			  AND (b.expiry_date >= CURDATE() OR b.expiry_date IS NULL)
			  AND sle.warehouse = %s
			GROUP BY b.name
			HAVING SUM(sle.actual_qty) > 0
			ORDER BY b.expiry_date ASC
			LIMIT 1
		""", (item_code, warehouse), as_dict=True)
		if batches:
			return batches[0].name

	# 3. Fallback: Any valid unexpired, unrecalled batch registered for this item
	batches = frappe.db.sql("""
		SELECT name
		FROM `tabBatch`
		WHERE item = %s
		  AND disabled = 0
		  AND (custom_recalled = 0 OR custom_recalled IS NULL)
		  AND (expiry_date >= CURDATE() OR expiry_date IS NULL)
		ORDER BY expiry_date ASC
		LIMIT 1
	""", (item_code,), as_dict=True)
	if batches:
		return batches[0].name

	return None


def auto_allocate_fefo_batches(doc, method=None):
	"""Assign the earliest valid FEFO batch to any batch-controlled item lacking one."""
	rows = doc.get("items") or doc.get("locations") or []
	for item in rows:
		if not item.get("item_code") or item.get("batch_no"):
			continue

		batch = get_auto_batch(item.item_code, item.get("warehouse"))
		if batch:
			item.batch_no = batch
