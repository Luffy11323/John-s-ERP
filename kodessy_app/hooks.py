app_name = "kodessy_app"
app_title = "Kodessy App"
app_publisher = "Kodessy"
app_description = "Pharma, Medical Device and Veterinary Distribution ERPNext Solution"
app_email = "info@kodessy.com"
app_license = "mit"

# Fixtures - loaded from fixtures/*.json on every bench migrate
# All records exported from the live Frappe Cloud DB to make the app standalone.
fixtures = [
    # Roles
    "Role",

    # Workflow engine
    "Workflow State",
    "Workflow Action Master",
    {
        "dt": "Workflow",
        "filters": [["name", "in", [
            "Customer",
            "Item V3",
            "Journal Entry",
            "Payment Entry",
            "Purchase Order Two-Tier Approval",
            "Quotation Approval Workflow",
            "Sales Order V3",
            "Stock Reconciliation Approval",
            "Supplier"
        ]]]
    },

    # Field & Form customisation
    "Custom Field",
    "Property Setter",

    # Print formats (all standard=No, safe to overwrite)
    # NOTE: notification.json, email_template.json and client_script.json have been
    # physically DELETED from fixtures/. Frappe v15 imports every JSON file that
    # exists in fixtures/ regardless of this list, so removing from this list alone
    # is not enough — the file must not exist.
    "Print Format",

    # Dashboards
    "Number Card",
    "Workspace",
]

doc_events = {
    "Quotation": {
        "validate": "kodessy_app.controllers.credit_control.check_customer_credit_limit"
    },
    "Sales Order": {
        "before_validate": "kodessy_app.controllers.fefo_control.auto_allocate_fefo_batches",
        "validate": [
            "kodessy_app.controllers.credit_control.check_customer_credit_limit",
            "kodessy_app.controllers.quarantine_control.validate_quarantine_stock"
        ]
    },
    "Pick List": {
        "validate": "kodessy_app.controllers.quarantine_control.validate_quarantine_stock"
    },
    "Delivery Note": {
        "before_validate": "kodessy_app.controllers.fefo_control.auto_allocate_fefo_batches",
        "validate": [
            "kodessy_app.controllers.fefo_control.auto_allocate_fefo_batches",
            "kodessy_app.controllers.quarantine_control.validate_quarantine_stock",
            "kodessy_app.controllers.returns_control.validate_sales_return"
        ]
    },
    "Sales Invoice": {
        "before_validate": "kodessy_app.controllers.fefo_control.auto_allocate_fefo_batches",
        "validate": [
            "kodessy_app.controllers.quarantine_control.validate_quarantine_stock",
            "kodessy_app.controllers.returns_control.validate_sales_return",
            "kodessy_app.controllers.credit_note_control.reset_approval_if_changed"
        ],
        "before_submit": "kodessy_app.controllers.credit_note_control.require_credit_note_approval"
    },
    "Purchase Receipt": {
        "validate": "kodessy_app.controllers.quarantine_control.route_receipt_to_quarantine"
    },
    "Stock Entry": {
        "validate": "kodessy_app.controllers.quarantine_control.validate_quarantine_release"
    },
    "Contact": {
        "validate": "kodessy_app.controllers.contact_control.sync_customer_primary_contact"
    }
}

# Workflow / submit / cancel notifications (role + owner) with timeline activity entries
from kodessy_app.controllers.workflow_notify import build_doc_events

for _dt, _events in build_doc_events().items():
    _existing = doc_events.setdefault(_dt, {})
    for _event, _handler in _events.items():
        _current = _existing.get(_event)
        if _current is None:
            _existing[_event] = _handler
        elif isinstance(_current, list):
            _current.append(_handler)
        else:
            _existing[_event] = [_current, _handler]

# Enable developer mode & server scripts for System Manager / Script Manager
doc_events.setdefault("Server Script", {})["before_validate"] = "kodessy_app.controllers.dev_access.enable_developer_mode"
doc_events.setdefault("Print Format", {})["before_validate"] = "kodessy_app.controllers.dev_access.enable_developer_mode"

before_request = ["kodessy_app.controllers.dev_access.enable_developer_mode"]
extend_bootinfo = "kodessy_app.controllers.dev_access.extend_bootinfo"


scheduler_events = {
    "daily": [
        "kodessy_app.tasks.flag_near_expiry"
    ]
}

doctype_js = {
    "Sales Invoice": "public/js/sales_invoice.js",
    "Batch": "public/js/batch.js",
    "Delivery Trip": "public/js/delivery_trip.js"
}

override_doctype_class = {
    "Delivery Trip": "kodessy_app.overrides.delivery_trip.CustomDeliveryTrip"
}

# Naming series, FEFO, roles, demo master data, custom fields, QC templates, workflows
after_migrate = "kodessy_app.setup_pharma.after_migrate"

# Glassmorphism & UI Optimization Assets (cache-busting v=20261021_notif_contrast_fix)
app_include_css = "/assets/kodessy_app/css/kodessy_glass.css?v=20261021_notif_contrast_fix"
app_include_js = "/assets/kodessy_app/js/kodessy_glass.js?v=20261021_notif_contrast_fix"

