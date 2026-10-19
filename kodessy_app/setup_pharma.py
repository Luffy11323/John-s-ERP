"""Idempotent pharma configuration applied on every `bench migrate`.

Every step is isolated: a failure in one step is logged to the Error Log and
never blocks the migration or the other steps.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from kodessy_app.setup_naming import apply_naming_series

DEMO_CREDIT_LIMITS = {
	"Raja Isteri Pengiran Anak Saleha (RIPAS) Hospital": 100000,
	"Jerudong Park Medical Centre (JPMC)": 75000,
	"Suri Seri Begawan Hospital": 50000,
	"Pengiran Muda Mahkota Pengiran Muda Haji Al-Muhtadee Billah Hospital": 30000,
	"Pengiran Isteri Hajah Mariam Hospital": 20000,
}

DEMO_ITEMS = ["AMOX-500", "INS-100", "PARAC-IV", "PULSE-OX", "VET-AMOX"]
EXTRA_UOMS = ["Box", "Pack", "Vial", "Bottle", "Pen", "Unit", "Nos"]
DEFAULT_SHELF_LIFE_DAYS = 730

QC_PARAMETERS = [
	"Physical Appearance",
	"Packaging Integrity",
	"Label & Batch Verification",
	"Certificate of Analysis (CoA) Present",
	"Temperature on Arrival",
]


def after_migrate():
	steps = [
		apply_naming_series,
		set_fefo_allocation,
		fix_workflow_roles,
		ensure_roles,
		ensure_uoms,
		ensure_supplier_groups,
		fix_demo_items,
		set_demo_credit_limits,
		ensure_custom_fields,
		make_return_fields_mandatory,
		ensure_quality_templates,
		ensure_stock_reconciliation_workflow,
		ensure_workflow_state_colors,
		ensure_print_formats,
		ensure_warehouse_mandatory,
		ensure_workflow_avoid_status_override,
		ensure_brunei_masters_and_currency,
	]
	for step in steps:
		try:
			step()
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"Kodessy setup step failed: {step.__name__}")


# --------------------------------------------------------------------------
# System settings / roles
# --------------------------------------------------------------------------
def set_fefo_allocation():
	"""FEFO: pick batches by earliest expiry instead of FIFO."""
	if frappe.get_meta("Stock Settings").has_field("pick_serial_and_batch_based_on"):
		frappe.db.set_single_value("Stock Settings", "pick_serial_and_batch_based_on", "Expiry")


def fix_workflow_roles():
	"""Safeguard: 'Finance Manager' is not a standard role; use 'Accounts Manager'."""
	if frappe.db.exists("Role", "Finance Manager"):
		return
	for doctype, field in (("Workflow Transition", "allowed"), ("Workflow Document State", "allow_edit")):
		frappe.db.set_value(doctype, {field: "Finance Manager"}, field, "Accounts Manager")


def ensure_roles():
	for role in ("Quality Unit",):
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def ensure_workflow_state_colors():
	"""Assign standard Frappe styles (Green, Red, Blue, Grey) to Workflow States."""
	color_map = {
		# Approved / Completed -> Green (Success)
		"Approved": "Success",
		"Approved and Paid": "Success",
		"Finalized": "Success",
		"Active": "Success",
		# Cancelled / Rejected -> Red (Danger)
		"Cancelled": "Danger",
		"Rejected": "Danger",
		# Pending / In Review -> Blue (Primary/Info)
		"Pending": "Primary",
		"Pending Approval": "Primary",
		"Pending Purchasing Manager Approval": "Primary",
		"Pending PM Approval": "Primary",
		"Pending Finance Approval": "Primary",
		"Pending Review": "Primary",
		"Pending Final Approval": "Primary",
		"Pending Warehouse Manager Approval": "Primary",
		"In Review": "Primary",
		"Changes Required": "Warning",
		"On Hold": "Warning",
		# Draft / Initial -> Info (Sky Blue)
		"Draft": "Info",
		"Initiated": "Info",
	}

	for state_name, style in color_map.items():
		if frappe.db.exists("Workflow State", state_name):
			frappe.db.set_value("Workflow State", state_name, "style", style)

	# Clean legacy/invalid icons that trigger Frappe's glyphicon validation error
	frappe.db.sql("UPDATE `tabWorkflow State` SET icon = '' WHERE icon LIKE 'octicon%'")


def ensure_print_formats():
	"""Ensure custom pharma print formats are marked standard='No' so operators can edit them in UI."""
	import os
	frappe.db.sql("UPDATE `tabPrint Format` SET standard = 'No' WHERE custom_format = 1 OR module = 'Kodessy App'")

	# Ensure Pharma Pick and Pack Slip has the latest template if present on disk
	template_path = os.path.join(os.path.dirname(__file__), "templates", "pharma_pick_and_pack_slip.html")
	if os.path.exists(template_path) and frappe.db.exists("Print Format", "Pharma Pick and Pack Slip"):
		with open(template_path, "r", encoding="utf-8") as f:
			html_content = f.read()
		frappe.db.set_value("Print Format", "Pharma Pick and Pack Slip", {
			"html": html_content,
			"standard": "No",
			"custom_format": 1
		})

	# Ensure Pick List defaults to Pharma Pick and Pack Slip
	if frappe.db.exists("DocType", "Pick List"):
		frappe.db.set_value("DocType", "Pick List", "default_print_format", "Pharma Pick and Pack Slip")
	ps_name = "Pick List-main-default_print_format"
	if not frappe.db.exists("Property Setter", ps_name):
		from frappe.custom.doctype.property_setter.property_setter import make_property_setter
		make_property_setter("Pick List", None, "default_print_format", "Pharma Pick and Pack Slip", "Data", for_doctype=True)



def ensure_warehouse_mandatory():
	"""Set target warehouse on PO and source warehouse on SO as mandatory via Property Setter.
	Using Property Setter allows users to disable or customize it from Customize Form UI at any time.
	"""
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter

	for doctype in ("Purchase Order Item", "Sales Order Item"):
		ps_name = f"{doctype}-warehouse-reqd"
		if not frappe.db.exists("Property Setter", ps_name):
			make_property_setter(
				doctype,
				"warehouse",
				"reqd",
				1,
				"Check",
				for_doctype=False,
				validate_fields_for_doctype=False,
			)


def ensure_workflow_avoid_status_override():
	"""Ensure 'Don't Override Status' (avoid_status_override) is checked on approved states (doc_status=1)
	so ERPNext shows native status (e.g. 'To Deliver and Bill', 'To Receive and Bill').
	Operators can uncheck this from the Workflow UI anytime.
	"""
	frappe.db.sql("UPDATE `tabWorkflow Document State` SET avoid_status_override = 1 WHERE doc_status = '1'")


# --------------------------------------------------------------------------
# Master data

# --------------------------------------------------------------------------
def ensure_uoms():
	for uom in EXTRA_UOMS:
		if not frappe.db.exists("UOM", uom):
			frappe.get_doc({"doctype": "UOM", "uom_name": uom, "enabled": 1}).insert(ignore_permissions=True)


def ensure_supplier_groups():
	"""Supplier Groups referenced by suppliers must exist, otherwise PO tax-rule lookup crashes."""
	groups = {s.supplier_group for s in frappe.get_all("Supplier", fields=["supplier_group"]) if s.supplier_group}
	for group in groups | {"Pharmaceutical Supplier", "Local Distributor"}:
		if not frappe.db.exists("Supplier Group", group):
			frappe.get_doc(
				{"doctype": "Supplier Group", "supplier_group_name": group, "parent_supplier_group": "All Supplier Groups"}
			).insert(ignore_permissions=True)


def fix_demo_items():
	"""Give demo pharma items a valid UOM table and shelf life so they can be transacted."""
	for code in DEMO_ITEMS:
		if not frappe.db.exists("Item", code):
			continue
		item = frappe.get_doc("Item", code)
		changed = False

		if item.stock_uom and not frappe.db.exists("UOM", item.stock_uom):
			frappe.get_doc({"doctype": "UOM", "uom_name": item.stock_uom, "enabled": 1}).insert(ignore_permissions=True)

		existing = {row.uom for row in item.get("uoms", [])}
		wanted = [item.stock_uom, "Box"] if item.stock_uom else ["Box"]
		for uom in wanted:
			if uom and uom not in existing:
				# NOTE: factor 1 is a neutral default; adjust to real pack conversion in the Item master.
				item.append("uoms", {"uom": uom, "conversion_factor": 1})
				existing.add(uom)
				changed = True

		if item.get("has_expiry_date") and not item.get("shelf_life_in_days"):
			item.shelf_life_in_days = DEFAULT_SHELF_LIFE_DAYS
			changed = True

		# custom_pack_size is mandatory on Item; backfill so the save below can succeed
		if frappe.get_meta("Item").has_field("custom_pack_size") and not item.get("custom_pack_size"):
			item.custom_pack_size = "1 {0}".format(item.stock_uom or "Unit")
			changed = True

		if changed:
			item.flags.ignore_validate_update_after_submit = True
			item.save(ignore_permissions=True)


def set_demo_credit_limits():
	for customer, limit in DEMO_CREDIT_LIMITS.items():
		if not frappe.db.exists("Customer", customer):
			frappe.get_doc({
				"doctype": "Customer",
				"customer_name": customer,
				"customer_group": "Commercial Hospital",
				"territory": "Brunei",
				"custom_credit_limit": limit,
			}).insert(ignore_permissions=True)
		else:
			frappe.db.set_value("Customer", customer, "custom_credit_limit", limit)


def ensure_brunei_masters_and_currency():
	"""Configure Currency, Country, and Demo Suppliers & Customers as per Brunei (BND)."""
	# 1. Currency BND
	if frappe.db.exists("Currency", "BND"):
		frappe.db.set_value("Currency", "BND", {
			"enabled": 1,
			"symbol": "B$",
			"fraction": "Sen",
			"fraction_units": 100
		})

	# 2. Global Defaults & Company
	for comp in frappe.get_all("Company", pluck="name"):
		frappe.db.set_value("Company", comp, {
			"default_currency": "BND",
			"country": "Brunei"
		})
	frappe.db.set_default("currency", "BND")
	frappe.db.set_default("country", "Brunei")

	# 3. Territory
	if not frappe.db.exists("Territory", "Brunei"):
		frappe.get_doc({
			"doctype": "Territory",
			"territory_name": "Brunei",
			"parent_territory": "All Territories"
		}).insert(ignore_permissions=True)

	# 4. Suppliers from guideline image
	suppliers = [
		("B. Braun", "Pharmaceutical Supplier"),
		("BD (Becton Dickinson)", "Pharmaceutical Supplier"),
		("Siemens Healthineers", "Pharmaceutical Supplier"),
		("Fresenius Kabi", "Pharmaceutical Supplier"),
		("Local medical supply distributors in Brunei", "Local Distributor"),
	]
	for supp_name, grp in suppliers:
		if not frappe.db.exists("Supplier", supp_name):
			frappe.get_doc({
				"doctype": "Supplier",
				"supplier_name": supp_name,
				"supplier_group": grp,
				"country": "Brunei"
			}).insert(ignore_permissions=True)

	# 5. Hide Manufacturing workspace
	if frappe.db.exists("Workspace", "Manufacturing"):
		frappe.db.set_value("Workspace", "Manufacturing", "is_hidden", 1)

	# 6. Set Favicon, App Logo, and Splash Image in Website Settings
	for field, val in [
		("app_logo", "/assets/kodessy_app/images/logo.png"),
		("favicon", "/assets/kodessy_app/images/favicon.png"),
		("splash_image", "/assets/kodessy_app/images/splash.png"),
		("app_name", "FIRMAI"),
	]:
		frappe.db.set_value("Website Settings", "Website Settings", field, val)
		frappe.db.set_value("Navbar Settings", "Navbar Settings", field, val)




# --------------------------------------------------------------------------
# Custom fields
# --------------------------------------------------------------------------
def _options_of(doctype, fieldname):
	field = frappe.get_meta(doctype).get_field(fieldname)
	return field.options if field else None


def ensure_custom_fields():
	fields = {
		"Batch": [
			{
				"fieldname": "custom_recalled",
				"label": "Recalled",
				"fieldtype": "Check",
				"insert_after": "disabled",
				"description": "Recalled batches cannot be picked, delivered or invoiced.",
			},
			{
				"fieldname": "custom_recall_reason",
				"label": "Recall Reason",
				"fieldtype": "Small Text",
				"insert_after": "custom_recalled",
				"depends_on": "custom_recalled",
				"mandatory_depends_on": "custom_recalled",
			},
			{
				"fieldname": "custom_near_expiry",
				"label": "Near Expiry",
				"fieldtype": "Check",
				"insert_after": "custom_recall_reason",
				"read_only": 1,
				"no_copy": 1,
				"description": "Set automatically by the daily near-expiry job.",
			},
		],
		"Supplier": [
			{
				"fieldname": "custom_lead_time_days",
				"label": "Typical Lead Time (Days)",
				"fieldtype": "Int",
				"insert_after": "supplier_type",
			},
		],
		"Sales Invoice": [
			{
				"fieldname": "custom_credit_note_approved_by",
				"label": "Credit Note Approved By",
				"fieldtype": "Link",
				"options": "User",
				"insert_after": "return_against",
				"read_only": 1,
				"no_copy": 1,
				"depends_on": "eval:doc.is_return",
			},
			{
				"fieldname": "custom_credit_note_approved_on",
				"label": "Credit Note Approved On",
				"fieldtype": "Datetime",
				"insert_after": "custom_credit_note_approved_by",
				"read_only": 1,
				"no_copy": 1,
				"depends_on": "eval:doc.is_return",
			},
		],
	}

	reason_options = _options_of("Sales Invoice Item", "custom_return_reason")
	assessment_options = _options_of("Sales Invoice Item", "custom_assessment_status")
	dn_item_fields = []
	if reason_options:
		dn_item_fields.append(
			{
				"fieldname": "custom_return_reason",
				"label": "Return Reason",
				"fieldtype": "Select",
				"options": reason_options,
				"insert_after": "item_name",
				"depends_on": "eval:parent.is_return",
				"mandatory_depends_on": "eval:parent.is_return",
			}
		)
	if assessment_options:
		dn_item_fields.append(
			{
				"fieldname": "custom_assessment_status",
				"label": "QA Assessment Status",
				"fieldtype": "Select",
				"options": assessment_options,
				"insert_after": "custom_return_reason",
				"depends_on": "eval:parent.is_return",
				"mandatory_depends_on": "eval:parent.is_return",
			}
		)
	if dn_item_fields:
		fields["Delivery Note Item"] = dn_item_fields

	create_custom_fields(fields, update=True)


def make_return_fields_mandatory():
	"""Return reason / QA assessment become mandatory on return documents and visible in grid row view."""
	for fieldname in ("custom_return_reason", "custom_assessment_status"):
		for dt in ("Sales Invoice Item", "Delivery Note Item"):
			name = f"{dt}-{fieldname}"
			if frappe.db.exists("Custom Field", name):
				frappe.db.set_value(
					"Custom Field",
					name,
					{
						"mandatory_depends_on": "eval:parent.is_return",
						"depends_on": "eval:parent.is_return",
						"in_list_view": 1,
						"columns": 2,
					},
				)
	for doctype in ("Sales Invoice Item", "Delivery Note Item"):
		frappe.clear_cache(doctype=doctype)


# --------------------------------------------------------------------------
# Quality templates
# --------------------------------------------------------------------------
def ensure_quality_templates():
	for parameter in QC_PARAMETERS:
		if not frappe.db.exists("Quality Inspection Parameter", parameter):
			frappe.get_doc(
				{"doctype": "Quality Inspection Parameter", "parameter": parameter, "description": parameter}
			).insert(ignore_permissions=True)

	template = "Pharma Incoming Inspection"
	if not frappe.db.exists("Quality Inspection Template", template):
		frappe.get_doc(
			{
				"doctype": "Quality Inspection Template",
				"quality_inspection_template_name": template,
				"item_quality_inspection_parameter": [
					{"specification": p, "numeric": 0, "value": "Acceptable"} for p in QC_PARAMETERS
				],
			}
		).insert(ignore_permissions=True)


# --------------------------------------------------------------------------
# Stock Reconciliation approval workflow
# --------------------------------------------------------------------------
def _ensure_state(name, style="Primary"):
	if not frappe.db.exists("Workflow State", name):
		frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": name, "style": style}).insert(
			ignore_permissions=True
		)


def _ensure_action(name):
	if not frappe.db.exists("Workflow Action Master", name):
		frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": name}).insert(
			ignore_permissions=True
		)


def ensure_stock_reconciliation_workflow():
	name = "Stock Reconciliation Approval"
	if frappe.db.exists("Workflow", name):
		return

	for state in ("Draft", "Pending Warehouse Manager Approval", "Approved", "Rejected"):
		_ensure_state(state)
	for action in ("Submit for Approval", "Approve", "Reject"):
		_ensure_action(action)

	frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": name,
			"document_type": "Stock Reconciliation",
			"is_active": 1,
			"workflow_state_field": "workflow_state",
			"states": [
				{"state": "Draft", "doc_status": 0, "allow_edit": "Stock User"},
				{"state": "Pending Warehouse Manager Approval", "doc_status": 0, "allow_edit": "Stock Manager"},
				{"state": "Approved", "doc_status": 1, "allow_edit": "Stock Manager"},
				{"state": "Rejected", "doc_status": 0, "allow_edit": "Stock Manager"},
			],
			"transitions": [
				{
					"state": "Draft",
					"action": "Submit for Approval",
					"next_state": "Pending Warehouse Manager Approval",
					"allowed": "Stock User",
				},
				{
					"state": "Pending Warehouse Manager Approval",
					"action": "Approve",
					"next_state": "Approved",
					"allowed": "Stock Manager",
				},
				{
					"state": "Pending Warehouse Manager Approval",
					"action": "Reject",
					"next_state": "Rejected",
					"allowed": "Stock Manager",
				},
			],
		}
	).insert(ignore_permissions=True)
