# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from kodessy_app.controllers.returns_control import validate_sales_return

APPROVER_ROLES = {"Accounts Manager", "Finance Manager", "System Manager"}


def reset_approval_if_changed(doc, method=None):
	"""Editing the amount of an approved credit note invalidates the approval."""
	if not doc.get("is_return") or doc.is_new():
		return
	before = doc.get_doc_before_save()
	if before and flt(before.grand_total) != flt(doc.grand_total):
		doc.custom_credit_note_approved_by = None
		doc.custom_credit_note_approved_on = None


def require_credit_note_approval(doc, method=None):
	if not doc.get("is_return"):
		return
	if not doc.get("custom_credit_note_approved_by"):
		frappe.throw(
			_("Credit Note {0} must be approved by a Finance Manager before it can be submitted. Use <b>Approve Credit Note</b>.").format(doc.name),
			title=_("Credit Note Approval Required"),
		)


@frappe.whitelist()
def approve_credit_note(name):
	doc = frappe.get_doc("Sales Invoice", name)
	if not doc.is_return:
		frappe.throw(_("{0} is not a credit note.").format(name))
	if doc.docstatus != 0:
		frappe.throw(_("Only draft credit notes can be approved."))

	user = frappe.session.user
	if not (set(frappe.get_roles(user)) & APPROVER_ROLES):
		frappe.throw(_("Only Accounts / Finance Managers can approve credit notes."), frappe.PermissionError)
	if user == doc.owner and user != "Administrator":
		frappe.throw(_("You cannot approve a credit note that you created."), frappe.PermissionError)

	# approved return = reason + QA assessment recorded on every line
	validate_sales_return(doc)

	doc.db_set("custom_credit_note_approved_by", user)
	doc.db_set("custom_credit_note_approved_on", now_datetime())
	return {"approved_by": user}
