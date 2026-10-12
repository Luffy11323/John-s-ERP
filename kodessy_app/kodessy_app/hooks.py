app_name = "kodessy_app"
app_title = "Kodessy App"
app_publisher = "Kodessy"
app_description = "Custom ERPNext Extensions for Sales, Fulfilment, Procurement, and Finance"
app_email = "info@kodessy.com"
app_license = "mit"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/kodessy_app/css/kodessy_app.css"
# app_include_js = "/assets/kodessy_app/js/kodessy_app.js"

# include js, css files in header of web template
# web_include_css = "/assets/kodessy_app/css/kodessy_app.css"
# web_include_js = "/assets/kodessy_app/js/kodessy_app.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "kodessy_app.utils.jinja_methods",
# 	"filters": "kodessy_app.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "kodessy_app.install.before_install"
# after_install = "kodessy_app.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "kodessy_app.uninstall.before_uninstall"
# after_uninstall = "kodessy_app.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kodessy_app.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"Quotation": {
# 		"validate": "kodessy_app.sales.quotation.validate",
# 		"on_submit": "kodessy_app.sales.quotation.on_submit",
# 	},
# 	"Sales Order": {
# 		"on_submit": "kodessy_app.sales.sales_order.on_submit",
# 	},
# 	"Purchase Order": {
# 		"on_submit": "kodessy_app.procurement.purchase_order.on_submit",
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"kodessy_app.tasks.all"
# 	],
# 	"daily": [
# 		"kodessy_app.tasks.daily"
# 	],
# 	"hourly": [
# 		"kodessy_app.tasks.hourly"
# 	],
# 	"weekly": [
# 		"kodessy_app.tasks.weekly"
# 	],
# 	"monthly": [
# 		"kodessy_app.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "kodessy_app.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "kodessy_app.event.get_events"
# }
