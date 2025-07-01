from . import __version__ as app_version

app_name = "supportdesk"
app_title = "supportdesk"
app_publisher = "Wahni IT Solutions Pvt Ltd"
app_description = "Your guide to unlocking full potential of ERPNext"
app_email = "support@wahni.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/supportdesk/css/supportdesk.css"
app_include_js = ["supportdesk.bundle.js"]

# include js, css files in header of web template
# web_include_css = "/assets/supportdesk/css/supportdesk.css"
# web_include_js = "/assets/supportdesk/js/supportdesk.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "supportdesk/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"User": "public/js/impersonation.js","Comment": "public/js/comment2.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Boot Info
extend_bootinfo = "supportdesk.boot.set_bootinfo"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "supportdesk.utils.jinja_methods",
#	"filters": "supportdesk.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "supportdesk.install.before_install"
after_install = "supportdesk.setup.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "supportdesk.uninstall.before_uninstall"
# after_uninstall = "supportdesk.uninstall.after_uninstall"


# Migration
# ------------
after_migrate = "supportdesk.setup.migrate.after_migrate"


# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "supportdesk.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    "": "your_custom_app.sales_invoice_override.CustomSalesInvoice"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Comment": {
		"after_insert": "supportdesk.custom_comment.after_insert"
	}
}

# on_session_creation = "supportdesk.custom_comment.on_session_creation"

# Scheduled Tasks
# ---------------

scheduler_events = {
#	"all": [
#		"supportdesk.tasks.all"
#	],
"cron": {
        "* * * * *": "supportdesk.utils.support.auto_close_tickets"
    }
#	"daily": [
#		"supportdesk.tasks.daily"
#	],
	# "hourly": [
	# 	"supportdesk.support.auto_close_tickets"
	# ],
#	"weekly": [
#		"supportdesk.tasks.weekly"
#	],
#	"monthly": [
#		"supportdesk.tasks.monthly"
	# ],
}

# Testing
# -------

# before_tests = "supportdesk.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "supportdesk.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "supportdesk.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"supportdesk.auth.validate"
# ]
