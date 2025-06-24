# Copyright (c) 2023, Wahni IT Solutions Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from genie.utils.requests import make_request


class GenieSettings(Document):
	def validate(self):
		# frappe.throw("validate")	
		self.validate_sp_access()

	def validate_sp_access(self):
		if not self.enable_ticket_raising:
			return

		else:

			headers = {
				"Authorization": f"token {self.get_password('support_api_token')}",
			}

			support_portal = make_request(
				url=f"{self.support_url}/api/method/frappe.utils.change_log.get_versions",
				headers=headers,
				payload={}
			).get("message")

			# if not support_portal.get("helpdesk"):
			# 	frappe.throw(_("{0} does not have Helpdesk app installed.").format(self.support_url))
			# self.role_permission()

	def role_permission(self):		
		self.assign_role_to_user("support") 
		self.support_role_permission("Ticket Details", 'Support')
		# 1f97aab59b4b908:a58d1d274324ada

	def assign_role_to_user(self, role_name):
		if not frappe.db.exists("User", "support@bizmap.in"):

			frappe.throw("user not exist")	
			frappe.msgprint(_("User does not exist"))
			return

		user = frappe.get_doc("User", "support@bizmap.in")
		if role_name not in [role.role for role in user.roles]:

			# frappe.throw("support role exist")	
			user.append("roles", {"role": role_name})
			user.save(ignore_permissions=True)
			frappe.db.commit()
			frappe.msgprint(_("Role '{0}' assigned to {1}").format(role_name, "support@bizmap.in"))
		

	def support_role_permission(self, doctype, role):
    # Check if the permission already exists
		if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role}):
			# Create a new Custom DocPerm entry for the role
			permission = frappe.get_doc({
				"doctype": "Custom DocPerm",
				"parent": doctype,
				"role": role,
				"read": 1,  # Grant Read access
				"create": 1,  # Grant Create access
				"write": 0,   # Optional: Add Write access (1 if required)
				"delete": 0,  # Optional: Add Delete access (1 if required)
				"submit": 0,
				"cancel": 0,
				"amend": 0,
			})
			permission.insert(ignore_permissions=True)
			frappe.db.commit()
			frappe.msgprint(f"Permissions for '{doctype}' have been granted to the '{role}' role.")
		else:
			frappe.msgprint(f"'{role}' role already has permissions for '{doctype}'.")