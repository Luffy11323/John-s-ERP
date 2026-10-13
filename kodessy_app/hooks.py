app_name = "kodessy_app"
app_title = "Kodessy App"
app_publisher = "Kodessy"
app_description = "Pharma, Medical Device and Veterinary Distribution ERPNext Solution"
app_email = "info@kodessy.com"
app_license = "mit"

# Export fixtures for bench migrate
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["module", "in", ["Kodessy App", "Selling", "Stock", "Accounts"]]]
    },
    {
        "dt": "Workflow",
        "filters": [["workflow_name", "in", ["Quotation Approval Workflow", "Purchase Order Two-Tier Approval"]]]
    },
    {
        "dt": "Workflow State"
    },
    {
        "dt": "Workflow Action Master"
    },
    {
        "dt": "Print Format"
    }
]

doc_events = {
    "Quotation": {
        "validate": "kodessy_app.controllers.credit_control.check_customer_credit_limit"
    },
    "Sales Order": {
        "validate": [
            "kodessy_app.controllers.credit_control.check_customer_credit_limit",
            "kodessy_app.controllers.quarantine_control.validate_quarantine_stock"
        ]
    },
    "Pick List": {
        "validate": "kodessy_app.controllers.quarantine_control.validate_quarantine_stock"
    },
    "Delivery Note": {
        "validate": [
            "kodessy_app.controllers.quarantine_control.validate_quarantine_stock",
            "kodessy_app.controllers.fefo_control.auto_allocate_fefo_batches",
            "kodessy_app.controllers.returns_control.validate_sales_return"
        ]
    },
    "Sales Invoice": {
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
    }
}

scheduler_events = {
    "daily": [
        "kodessy_app.tasks.flag_near_expiry"
    ]
}

doctype_js = {
    "Sales Invoice": "public/js/sales_invoice.js",
    "Batch": "public/js/batch.js"
}

# Naming series, FEFO, roles, demo master data, custom fields, QC templates, workflows
after_migrate = "kodessy_app.setup_pharma.after_migrate"

# Glassmorphism & UI Optimization Assets
app_include_css = "/assets/kodessy_app/css/kodessy_glass.css"
app_include_js = "/assets/kodessy_app/js/kodessy_glass.js"
