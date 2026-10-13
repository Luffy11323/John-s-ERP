# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.utils import getdate, nowdate

QUARANTINE_KEYWORDS = ["quarantine", "near-expiry", "reject"]
RELEASE_ROLES = {"Quality Manager", "Quality Unit", "System Manager"}


def _is_restricted(warehouse):
	warehouse = (warehouse or "").lower()
	return any(k in warehouse for k in QUARANTINE_KEYWORDS)


def validate_quarantine_stock(doc, method=None):
	"""Block quarantined / near-expiry / rejected warehouses and recalled or expired batches.

	Customer returns are allowed to land in quarantine, so returns are skipped.
	"""
	if doc.get("is_return"):
		return

	rows = doc.get("items") or doc.get("locations") or []
	has_recall_field = frappe.get_meta("Batch").has_field("custom_recalled")

	for item in rows:
		if _is_restricted(item.get("warehouse")):
			frappe.throw(
				_("Cannot sell or dispatch item {0} from restricted warehouse: <b>{1}</b>. Stock must be formally released by Quality Unit.").format(
					item.item_code, item.warehouse
				),
				title=_("Quarantine Restriction"),
			)

		batch_no = item.get("batch_no")
		if not batch_no:
			continue

		fields = ["expiry_date", "disabled"] + (["custom_recalled"] if has_recall_field else [])
		batch = frappe.db.get_value("Batch", batch_no, fields, as_dict=True)
		if not batch:
			continue
		if has_recall_field and batch.custom_recalled:
			frappe.throw(
				_("Row #{0}: Batch <b>{1}</b> has been <b>recalled</b> and cannot be allocated or sold.").format(item.idx, batch_no),
				title=_("Recalled Batch"),
			)
		if batch.expiry_date and getdate(batch.expiry_date) < getdate(nowdate()):
			frappe.throw(
				_("Row #{0}: Batch <b>{1}</b> expired on {2} and cannot be allocated or sold.").format(
					item.idx, batch_no, batch.expiry_date
				),
				title=_("Expired Batch"),
			)


def _quarantine_warehouse(company):
	return frappe.db.get_value(
		"Warehouse",
		{"warehouse_name": ["like", "Quarantine%"], "company": company, "is_group": 0, "disabled": 0},
		"name",
	)


def route_receipt_to_quarantine(doc, method=None):
	"""Items that need QC release are received into Quarantine, never straight into saleable stock."""
	if not doc.is_new() or doc.get("is_return"):
		return
	quarantine = _quarantine_warehouse(doc.company)
	if not quarantine:
		return

	moved = []
	for item in doc.get("items", []):
		if not frappe.db.get_value("Item", item.item_code, "custom_requires_qc_release"):
			continue
		if _is_restricted(item.get("warehouse")):
			continue
		item.warehouse = quarantine
		moved.append(item.item_code)

	if moved:
		frappe.msgprint(
			_("Received into <b>{0}</b> pending Quality Unit release: {1}").format(quarantine, ", ".join(moved)),
			indicator="orange",
			alert=True,
		)


def validate_quarantine_release(doc, method=None):
	"""Only the Quality Unit may move stock out of Quarantine."""
	if doc.get("stock_entry_type") not in ("Material Transfer", "Material Issue") and doc.get("purpose") not in (
		"Material Transfer",
		"Material Issue",
	):
		return

	for row in doc.get("items", []):
		source = (row.get("s_warehouse") or "").lower()
		if "quarantine" in source and not (set(frappe.get_roles()) & RELEASE_ROLES):
			frappe.throw(
				_("Row #{0}: Only the Quality Unit can release stock from {1}.").format(row.idx, row.s_warehouse),
				title=_("Quality Release Required"),
			)
