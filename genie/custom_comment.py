
import frappe
import requests

import json
from genie.utils.requests import make_request

import frappe
from frappe.utils import get_url



@frappe.whitelist()
def after_insert(doc, method):
	if doc.reference_doctype == "Ticket Details":
		if doc.custom_is_system_generated == 0  and doc.comment_type == "Comment":
			# Check if the comment is from the host
			client_comment(doc)
		else:
			user = frappe.db.get_value("User", {"full_name": doc.comment_email}, "name")
			if user:
				send_notification(user, doc)

@frappe.whitelist()
def client_comment(doc):
	settings = frappe.get_cached_doc("Genie Settings")

	headers = {
		"Authorization": f"token {settings.get_password('support_api_token')}"
	}

	if isinstance(doc, str):
		doc = frappe.get_doc("Comment", doc)  # Fetch the document if `doc` is a name or ID
	doc_dict = doc.as_dict()
	frappe.log_error(f"Settings: {settings.as_dict()}\nHeaders: {headers}\nURL: {settings.support_url}", "Debug Info")

	payload = {
		"doc": doc_dict  
	}
	
	try:
		response = requests.post(
			url=f"{settings.support_url}/api/method/supportsystem.supportsystem.custom.custom_api.received_comment",
			headers=headers,
			json=payload,  
			timeout=10  # Optional timeout
		)
		response.raise_for_status()

		# Log and return the response
		frappe.log_error(f"API Response: {response.json()}", "API Success")
		return response.json()

	except requests.exceptions.HTTPError as e:
		# Log error details
		error_message = f"HTTPError: {e}, Response: {response.text}"
		frappe.log_error(error_message, "API Error")
		frappe.throw(f"API returned an error: {response.status_code} - {response.text}")

	except Exception as e:
		# Log unexpected exceptions
		error_message = f"Unexpected Error: {str(e)}"
		frappe.log_error(error_message, "API Error")
		frappe.throw("An unexpected error occurred while calling the API.")


@frappe.whitelist()
def send_notification(user, doc):
	ticket = frappe.get_doc(doc.reference_doctype, doc.reference_name)
	notification_log = frappe.get_doc({
		"doctype": "Notification Log",
		"subject": f"You received a new comment on your ticket {doc.reference_name}",
		"for_user": ticket.owner,
		"document_type": doc.reference_doctype,
		"document_name": doc.reference_name,
		"from_user": doc.owner,
		"type": "Alert"
	})
	notification_log.insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.db.set_value("Notification Log", notification_log.name, "owner", notification_log.for_user)
	frappe.db.commit()