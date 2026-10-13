import frappe
from frappe.utils import flt, nowdate, add_days, getdate

# slug -> (title, subtitle, builder key)
SECTIONS = {
	"home": ("Kodessy Overview", "Pharma distribution at a glance"),
	"selling": ("Sales & Distribution", "Quotations, orders and deliveries"),
	"buying": ("Procurement", "Purchase orders and supplier receipts"),
	"stock": ("Warehouse & Quality", "FEFO, quarantine and stock health"),
	"accounting": ("Finance", "Receivables, payables and credit notes"),
}


def _count(doctype, filters=None):
	if not frappe.has_permission(doctype, "read"):
		return 0
	return frappe.db.count(doctype, filters or {})


def _sum(doctype, field, filters=None):
	if not frappe.has_permission(doctype, "read"):
		return 0
	rows = frappe.get_all(doctype, filters=filters or {}, fields=[f"sum({field}) as v"])
	return flt(rows[0].v) if rows else 0


def _kpi(label, value, route, fmt="num", icon=""):
	return {"label": label, "value": value, "route": route, "fmt": fmt, "icon": icon}


def _selling():
	return [
		_kpi("Draft Quotations", _count("Quotation", {"docstatus": 0}), "quotation?docstatus=0"),
		_kpi("Pending Sales Manager Approval", _count("Quotation", {"workflow_state": "Pending Sales Manager Approval"}), "quotation?workflow_state=Pending%20Sales%20Manager%20Approval"),
		_kpi("Open Sales Orders", _count("Sales Order", {"docstatus": 1, "status": ["in", ["To Deliver and Bill", "To Deliver", "To Bill"]]}), "sales-order?docstatus=1"),
		_kpi("Pending Deliveries", _count("Delivery Note", {"docstatus": 0}), "delivery-note?docstatus=0"),
		_kpi("Unpaid Sales Invoices", _count("Sales Invoice", {"docstatus": 1, "outstanding_amount": [">", 0]}), "sales-invoice?outstanding_amount=%5B%22%3E%22%2C0%5D"),
		_kpi("Outstanding Receivable (MYR)", _sum("Sales Invoice", "outstanding_amount", {"docstatus": 1}), "sales-invoice", "money"),
	]


def _buying():
	return [
		_kpi("Draft Purchase Orders", _count("Purchase Order", {"docstatus": 0}), "purchase-order?docstatus=0"),
		_kpi("Pending Purchasing Approval", _count("Purchase Order", {"workflow_state": "Pending Purchasing Manager Approval"}), "purchase-order?workflow_state=Pending%20Purchasing%20Manager%20Approval"),
		_kpi("Pending Finance Approval", _count("Purchase Order", {"workflow_state": "Pending Finance Approval"}), "purchase-order?workflow_state=Pending%20Finance%20Approval"),
		_kpi("To Receive", _count("Purchase Order", {"docstatus": 1, "status": ["in", ["To Receive and Bill", "To Receive"]]}), "purchase-order?docstatus=1"),
		_kpi("Open Material Requests", _count("Material Request", {"docstatus": 1, "status": ["in", ["Pending", "Partially Ordered"]]}), "material-request"),
		_kpi("Unpaid Purchase Invoices (MYR)", _sum("Purchase Invoice", "outstanding_amount", {"docstatus": 1}), "purchase-invoice", "money"),
	]


def _stock():
	soon = add_days(nowdate(), 90)
	near_expiry = _count("Batch", {"disabled": 0, "expiry_date": ["between", [nowdate(), soon]]})
	expired = _count("Batch", {"disabled": 0, "expiry_date": ["<", nowdate()]})
	return [
		_kpi("Batches Expiring (90 days)", near_expiry, "batch?expiry_date=%5B%22Between%22%2C%5B%22" + nowdate() + "%22%2C%22" + soon + "%22%5D%5D"),
		_kpi("Expired Batches", expired, "batch?expiry_date=%5B%22%3C%22%2C%22" + nowdate() + "%22%5D"),
		_kpi("Pending Purchase Receipts", _count("Purchase Receipt", {"docstatus": 0}), "purchase-receipt?docstatus=0"),
		_kpi("Quality Inspections Pending", _count("Quality Inspection", {"docstatus": 0}), "quality-inspection?docstatus=0"),
		_kpi("Open Pick Lists", _count("Pick List", {"docstatus": 0}), "pick-list?docstatus=0"),
		_kpi("Stock Reconciliations (Draft)", _count("Stock Reconciliation", {"docstatus": 0}), "stock-reconciliation?docstatus=0"),
	]


def _accounting():
	return [
		_kpi("Receivable (MYR)", _sum("Sales Invoice", "outstanding_amount", {"docstatus": 1}), "sales-invoice", "money"),
		_kpi("Payable (MYR)", _sum("Purchase Invoice", "outstanding_amount", {"docstatus": 1}), "purchase-invoice", "money"),
		_kpi("Overdue Sales Invoices", _count("Sales Invoice", {"docstatus": 1, "outstanding_amount": [">", 0], "due_date": ["<", nowdate()]}), "sales-invoice"),
		_kpi("Credit Notes (Returns)", _count("Sales Invoice", {"docstatus": 1, "is_return": 1}), "sales-invoice?is_return=1"),
		_kpi("Draft Payments", _count("Payment Entry", {"docstatus": 0}), "payment-entry?docstatus=0"),
		_kpi("Draft Journal Entries", _count("Journal Entry", {"docstatus": 0}), "journal-entry?docstatus=0"),
	]


def _home():
	return [
		_kpi("Pending Approvals", _count("Quotation", {"workflow_state": "Pending Sales Manager Approval"}) + _count("Purchase Order", {"workflow_state": ["in", ["Pending Purchasing Manager Approval", "Pending Finance Approval"]]}), "quotation"),
		_kpi("Open Sales Orders", _count("Sales Order", {"docstatus": 1, "status": ["in", ["To Deliver and Bill", "To Deliver", "To Bill"]]}), "sales-order"),
		_kpi("Open Purchase Orders", _count("Purchase Order", {"docstatus": 1, "status": ["in", ["To Receive and Bill", "To Receive"]]}), "purchase-order"),
		_kpi("Receivable (MYR)", _sum("Sales Invoice", "outstanding_amount", {"docstatus": 1}), "sales-invoice", "money"),
		_kpi("Expired Batches", _count("Batch", {"disabled": 0, "expiry_date": ["<", nowdate()]}), "batch"),
		_kpi("Quality Inspections Pending", _count("Quality Inspection", {"docstatus": 0}), "quality-inspection"),
	]


BUILDERS = {
	"home": _home,
	"selling": _selling,
	"buying": _buying,
	"stock": _stock,
	"accounting": _accounting,
}

# Report shortcuts rendered inside the same big card
REPORTS = {
	"stock": [
		["Batch-Wise Stock Balance", "query-report/Batch-Wise Balance History"],
		["Stock Ledger", "query-report/Stock Ledger"],
		["Stock Balance", "query-report/Stock Balance"],
	],
	"selling": [
		["Pending Sales Orders", "query-report/Pending SO Items For Purchase Request"],
		["Sales Analytics", "query-report/Sales Analytics"],
	],
	"buying": [
		["Purchase Order Analysis", "query-report/Purchase Order Analysis"],
		["Purchase Analytics", "query-report/Purchase Analytics"],
	],
	"accounting": [
		["Accounts Receivable", "query-report/Accounts Receivable"],
		["Accounts Payable", "query-report/Accounts Payable"],
		["General Ledger", "query-report/General Ledger"],
	],
	"home": [],
}


@frappe.whitelist()
def get_card(slug=None):
	slug = (slug or "home").lower()
	if slug not in BUILDERS:
		return None
	title, subtitle = SECTIONS[slug]
	return {
		"user": frappe.utils.get_fullname(frappe.session.user),
		"title": title,
		"subtitle": subtitle,
		"kpis": BUILDERS[slug](),
		"reports": [{"label": r[0], "route": r[1]} for r in REPORTS.get(slug, [])],
	}
