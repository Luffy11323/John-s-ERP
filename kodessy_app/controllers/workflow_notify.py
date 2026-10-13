# -*- coding: utf-8 -*-
"""Workflow / submit / cancel notifications.

For every workflow stage change, submit and cancel on tracked documents:
  * a Notification Log (bell icon) is sent to each user holding the approver role(s) + the document owner
  * an activity entry is added to the document timeline:
        Notification sent to <Role>
        <content>
Failures here never block the underlying transaction.
"""
import frappe
from frappe import _
from frappe.utils import get_url_to_form

# Doctypes that carry a workflow in this deployment plus the key transactional documents.
TRACKED_DOCTYPES = [
	"Quotation", "Sales Order", "Purchase Order", "Stock Reconciliation", "Payment Entry",
	"Journal Entry", "Customer", "Supplier", "Item", "Internal Store Request", "Payment Request",
	"Delivery Note", "Sales Invoice", "Purchase Receipt", "Purchase Invoice", "Stock Entry",
	"Quality Inspection", "Pick List",
]

# Used on submit/cancel when the doctype has no workflow transitions to derive roles from.
DEFAULT_ROLES = {
	"Delivery Note": ["Stock Manager"],
	"Pick List": ["Stock Manager"],
	"Purchase Receipt": ["Stock Manager", "Quality Unit"],
	"Stock Entry": ["Stock Manager"],
	"Quality Inspection": ["Quality Unit"],
	"Sales Invoice": ["Accounts Manager"],
	"Purchase Invoice": ["Accounts Manager"],
	"Payment Entry": ["Accounts Manager"],
	"Journal Entry": ["Accounts Manager"],
}

SKIP_USERS = {"Administrator", "Guest"}


def _active_workflow(doctype):
	return frappe.db.get_value("Workflow", {"document_type": doctype, "is_active": 1}, "name")


def _stage_roles(doc, state):
	"""Roles that can act on the document from its current workflow state (the next approvers)."""
	wf = _active_workflow(doc.doctype)
	if not wf:
		return []
	return [
		r for r in frappe.get_all(
			"Workflow Transition", filters={"parent": wf, "state": state}, pluck="allowed", distinct=True
		) if r
	]


def _all_workflow_roles(doctype):
	wf = _active_workflow(doctype)
	if not wf:
		return []
	return [
		r for r in frappe.get_all("Workflow Transition", filters={"parent": wf}, pluck="allowed", distinct=True) if r
	]


def _users_with_role(role):
	users = frappe.get_all("Has Role", filters={"role": role, "parenttype": "User"}, pluck="parent", distinct=True)
	if not users:
		return []
	return frappe.get_all("User", filters={"name": ["in", users], "enabled": 1}, pluck="name")


def _notify(doc, event_label, roles, detail=None):
	actor = frappe.session.user
	link = get_url_to_form(doc.doctype, doc.name)
	title = doc.get("title") or doc.name
	headline = _("{0} {1} - {2}").format(_(doc.doctype), doc.name, event_label)
	body = detail or ""
	content = "{0}{1}<br>{2}: {3}".format(
		headline, ("<br>" + body) if body else "", _("By"), actor
	)

	seen = set()

	def _send(user, who):
		if not user or user in SKIP_USERS or user == actor or user in seen:
			return
		seen.add(user)
		frappe.get_doc({
			"doctype": "Notification Log",
			"subject": "{0}: {1}".format(who, headline),
			"email_content": content,
			"for_user": user,
			"from_user": actor,
			"type": "Alert",
			"document_type": doc.doctype,
			"document_name": doc.name,
		}).insert(ignore_permissions=True)

	for role in dict.fromkeys(roles):
		users = _users_with_role(role)
		for user in users:
			_send(user, role)
		doc.add_comment(
			"Info",
			"Notification sent to <b>{0}</b> ({1} user{2})<br>{3}".format(
				role, len(users), "" if len(users) == 1 else "s", headline + (" - " + body if body else "")
			),
		)

	if doc.owner:
		_send(doc.owner, _("Owner"))
		doc.add_comment(
			"Info",
			"Notification sent to <b>Owner</b> ({0})<br>{1}".format(
				doc.owner, headline + (" - " + body if body else "")
			),
		)


def _safe(fn):
	def wrapper(doc, method=None):
		try:
			fn(doc, method)
		except Exception:
			frappe.log_error(title="Kodessy notification failed: {0} {1}".format(doc.doctype, doc.name))
	return wrapper


@_safe
def on_stage_change(doc, method=None):
	if not doc.meta.has_field("workflow_state") or not doc.get("workflow_state"):
		return
	before = doc.get_doc_before_save()
	if before and before.get("workflow_state") == doc.workflow_state:
		return
	state = doc.workflow_state
	_notify(doc, _("moved to {0}").format(state), _stage_roles(doc, state), detail=_("Stage: {0}").format(state))


@_safe
def on_submit(doc, method=None):
	roles = _all_workflow_roles(doc.doctype) or DEFAULT_ROLES.get(doc.doctype, [])
	_notify(doc, _("submitted"), roles)


@_safe
def on_cancel(doc, method=None):
	roles = _all_workflow_roles(doc.doctype) or DEFAULT_ROLES.get(doc.doctype, [])
	_notify(doc, _("cancelled"), roles)


def build_doc_events():
	return {
		dt: {
			"on_update": "kodessy_app.controllers.workflow_notify.on_stage_change",
			"on_update_after_submit": "kodessy_app.controllers.workflow_notify.on_stage_change",
			"on_submit": "kodessy_app.controllers.workflow_notify.on_submit",
			"on_cancel": "kodessy_app.controllers.workflow_notify.on_cancel",
		}
		for dt in TRACKED_DOCTYPES
	}
