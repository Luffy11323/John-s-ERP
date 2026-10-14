# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from kodessy_app.controllers.returns_control import validate_sales_return

APPROVER_ROLES = {"Accounts Manager", "Finance Manager", "System Manager"}


def _return_lines_signature(doc):
    """Stable fingerprint of return-reason + QA-status across all items.
    Used to detect if either field was edited after approval was granted."""
    return tuple(
        (item.get("custom_return_reason") or "", item.get("custom_assessment_status") or "")
        for item in doc.get("items", [])
    )


def reset_approval_if_changed(doc, method=None):
    """Editing the amount OR removing/changing return reason / QA assessment
    on an approved credit note invalidates the approval so it must be
    re-approved before submit."""
    if not doc.get("is_return") or doc.is_new():
        return

    # No approval recorded yet → nothing to invalidate
    if not doc.get("custom_credit_note_approved_by"):
        return

    before = doc.get_doc_before_save()
    if not before:
        return

    amount_changed = flt(before.grand_total) != flt(doc.grand_total)
    lines_changed  = _return_lines_signature(before) != _return_lines_signature(doc)

    if amount_changed or lines_changed:
        doc.custom_credit_note_approved_by = None
        doc.custom_credit_note_approved_on = None
        frappe.msgprint(
            _("Approval has been reset because the credit note details were changed. "
              "Please re-approve before submitting."),
            indicator="orange",
            alert=True,
        )


def require_credit_note_approval(doc, method=None):
    """before_submit gate: credit note must have return reason, QA assessment
    on every line AND a Finance Manager approval stamp."""
    if not doc.get("is_return"):
        return

    # Re-run return-line validation at submit time so the guard cannot be
    # bypassed by clearing fields after approval (D1 defect fix).
    validate_sales_return(doc)

    if not doc.get("custom_credit_note_approved_by"):
        frappe.throw(
            _("Credit Note {0} must be approved by a Finance Manager before it can be "
              "submitted. Use <b>Approve Credit Note</b>.").format(doc.name),
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

    # Validate return reason + QA assessment on every line before stamping approval
    validate_sales_return(doc)

    doc.db_set("custom_credit_note_approved_by", user)
    doc.db_set("custom_credit_note_approved_on", now_datetime())
    return {"approved_by": user}
