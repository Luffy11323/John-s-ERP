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
    "Delivery Note": {
        "validate": [
            "kodessy_app.controllers.quarantine_control.validate_quarantine_stock",
            "kodessy_app.controllers.fefo_control.auto_allocate_fefo_batches"
        ]
    },
    "Sales Invoice": {
        "validate": [
            "kodessy_app.controllers.quarantine_control.validate_quarantine_stock",
            "kodessy_app.controllers.returns_control.validate_sales_return"
        ]
    }
}
