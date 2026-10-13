# -*- coding: utf-8 -*-
import frappe
from frappe.utils import add_days, nowdate

# Months-before-expiry threshold is "to be confirmed" in the SRS; 90 days is the working default.
NEAR_EXPIRY_DAYS = 90


def flag_near_expiry():
	"""Flag batches expiring within NEAR_EXPIRY_DAYS and alert Stock Managers about newly flagged ones."""
	if not frappe.get_meta("Batch").has_field("custom_near_expiry"):
		return

	today, limit = nowdate(), add_days(nowdate(), NEAR_EXPIRY_DAYS)

	due = frappe.get_all(
		"Batch",
		filters={"disabled": 0, "expiry_date": ["between", [today, limit]], "custom_near_expiry": 0},
		pluck="name",
	)
	for name in due:
		frappe.db.set_value("Batch", name, "custom_near_expiry", 1, update_modified=False)

	# clear flag on batches that are no longer near-expiry window (expired or extended)
	stale = frappe.get_all(
		"Batch",
		filters={"custom_near_expiry": 1},
		or_filters=[["expiry_date", "<", today], ["expiry_date", ">", limit]],
		pluck="name",
	)
	for name in stale:
		frappe.db.set_value("Batch", name, "custom_near_expiry", 0, update_modified=False)

	if due:
		_notify(due)


def _notify(batches):
	users = frappe.get_all(
		"Has Role",
		filters={"role": "Stock Manager", "parenttype": "User"},
		pluck="parent",
		distinct=True,
	)
	users = [u for u in users if u not in ("Administrator", "Guest") and frappe.db.get_value("User", u, "enabled")]
	description = (
		"Batches entering the near-expiry window ({0} days). Review and move to Near-Expiry Bin: {1}".format(
			NEAR_EXPIRY_DAYS, ", ".join(batches[:25])
		)
	)
	for user in users:
		frappe.get_doc(
			{"doctype": "ToDo", "allocated_to": user, "description": description, "priority": "High"}
		).insert(ignore_permissions=True)
