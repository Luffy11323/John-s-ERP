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
from frappe.utils import escape_html, fmt_money, get_url_to_form

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


def _detail_rows(doc):
	"""(label, value) pairs for whichever of these fields the document has."""
	rows = []
	party = (
		doc.get("customer_name") or doc.get("customer") or doc.get("supplier_name")
		or doc.get("supplier") or doc.get("party_name") or doc.get("party")
	)
	if party:
		label = _("Supplier") if (doc.get("supplier") or doc.get("supplier_name")) else _("Customer")
		rows.append((label, party))
	if doc.get("project"):
		rows.append((_("Project"), doc.get("project")))
	currency = doc.get("currency") or doc.get("company_currency")
	if currency:
		rows.append((_("Currency"), currency))
	total = doc.get("grand_total") or doc.get("rounded_total") or doc.get("total_amount") or doc.get("paid_amount")
	if total:
		try:
			rows.append((_("Total"), fmt_money(total, currency=currency), True))
		except Exception:
			rows.append((_("Total"), str(total), True))
	return rows


def _card_html(doc, event_label, detail, actor, link):
	"""Styled notification card: heading, summary, detail table, Open button."""
	dt = escape_html(_(doc.doctype))
	cell = "padding:8px 0;border-bottom:1px solid #e5e7eb;"
	rows_html = ""
	for row in _detail_rows(doc):
		bold = len(row) > 2
		rows_html += (
			"<tr><td style='{c}color:#6b7280;'>{k}</td>"
			"<td style='{c}text-align:right;{b}'>{v}</td></tr>"
		).format(
			c=cell, k=escape_html(row[0]), v=escape_html(str(row[1])),
			b="font-weight:700;" if bold else "",
		)
	table = (
		"<table style='width:100%;border-collapse:collapse;font-size:13px;margin:12px 0;'>{0}</table>".format(rows_html)
		if rows_html else ""
	)
	stage = ("<div style='color:#6b7280;font-size:12px;'>{0}</div>".format(escape_html(detail))) if detail else ""
	return (
		"<div style='border-left:4px solid #10b981;background:#fff;border-radius:8px;"
		"padding:14px 16px;max-width:520px;font-family:inherit;'>"
		"<div style='font-size:12px;font-weight:700;letter-spacing:.5px;color:#065f46;"
		"text-transform:uppercase;'>{dt} {ev}</div>"
		"<div style='margin-top:8px;font-size:14px;'>{dt} <b>{name}</b> {ev}.</div>"
		"{stage}{table}"
		"<div style='color:#6b7280;font-size:12px;margin-bottom:10px;'>{by}: {actor}</div>"
		"<a href='{link}' style='display:inline-block;background:#10b981;color:#fff;"
		"padding:8px 16px;border-radius:6px;text-decoration:none;font-weight:600;'>{open} {dt}</a>"
		"</div>"
	).format(
		dt=dt, ev=escape_html(event_label), name=escape_html(doc.name), stage=stage, table=table,
		by=escape_html(_("By")), actor=escape_html(actor), link=escape_html(link), open=escape_html(_("Open")),
	)


def _notify(doc, event_label, roles, detail=None):
	actor = frappe.session.user
	link = get_url_to_form(doc.doctype, doc.name)
	title = doc.get("title") or doc.name
	headline = _("{0} {1} - {2}").format(_(doc.doctype), doc.name, event_label)
	body = detail or ""
	content = _card_html(doc, event_label, body, actor, link)

	seen_users = set()
	role_list = [r for r in dict.fromkeys(roles) if r]

	# 1. Send individual Notification Log (bell icon) to each actual recipient
	def _send(user, who):
		if not user or user in SKIP_USERS or user == actor or user in seen_users:
			return
		seen_users.add(user)
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

	# 2. Collect unique emails across all roles
	all_emails = []
	seen_emails = set()

	for role in role_list:
		users = _users_with_role(role)
		for u in users:
			_send(u, role)
			# Only emails, skipping internal system accounts like Administrator / Guest
			if u not in SKIP_USERS:
				email = frappe.db.get_value("User", u, "email") or u
				if "@" in email and email not in seen_emails:
					seen_emails.add(email)
					all_emails.append(email)

	# Also notify owner if owner not in seen_users
	if doc.owner and doc.owner not in seen_users:
		_send(doc.owner, _("Owner"))
		if doc.owner not in SKIP_USERS:
			owner_email = frappe.db.get_value("User", doc.owner, "email") or doc.owner
			if "@" in owner_email and owner_email not in seen_emails:
				seen_emails.add(owner_email)
				all_emails.append(owner_email)

	# Fallback if testing solely as Administrator
	if not all_emails:
		for role in role_list:
			for u in _users_with_role(role):
				email = frappe.db.get_value("User", u, "email") or u
				if "@" in email and email not in seen_emails:
					seen_emails.add(email)
					all_emails.append(email)

	# 3. Post a SINGLE combined activity comment box rather than individual duplicates
	target_roles = ", ".join(role_list) if role_list else _("Recipients")
	emails_display = ", ".join(all_emails) if all_emails else "no emails"

	doc.add_comment(
		"Info",
		"Notification sent to <b>{0}</b> ({1})<br>{2}".format(
			target_roles, emails_display, content
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
