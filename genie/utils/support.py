# Copyright (c) 2023, Wahni IT Solutions Pvt. Ltd. and contributors
# For license information, please see license.txt

import re
import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Concat_ws
from frappe.utils import cint, flt, get_url, now
from frappe.utils.safe_exec import get_safe_globals, safe_eval
import requests
from genie.utils.requests import make_request


@frappe.whitelist()
def create_local_ticket(subject, description, category, screen_recording):
	settings = frappe.get_cached_doc("Genie Settings")
	setting_details = generate_ticket_details(settings)

	description = re.sub(r'<[^>]+>', '', description)   ## convert from html to plaintext

	ticket = frappe.new_doc("Ticket Details")
	ticket.subject = subject
	ticket.description = description
	ticket.category = category
	ticket.status = setting_details.get('status')
	ticket.save()

	# str type variable
	if screen_recording != '':
		save_screen_recording(screen_recording, ticket.name)

	return ticket.name
	

def save_screen_recording(screen_recording_content, ticket_name):
	srname = screen_recording_content.split('/')[-1]

	# Fetch file by file URL instead of file_name
	file_doc = frappe.get_doc("File", {'file_url': screen_recording_content})
	
	file_doc.attached_to_doctype = "Ticket Details"
	file_doc.attached_to_name = ticket_name
	file_doc.is_private =True

	file_doc.save(ignore_permissions=True)
	frappe.db.commit()


@frappe.whitelist()
def received_host_comment(doc):
	cmt = frappe.new_doc("Comment")
	cmt.comment_type = "Comment"
	cmt.reference_doctype = "Ticket Details"
	cmt.reference_name = doc['client_ticket']
	cmt.comment_email = doc['comment_email']
	cmt.comment_by = doc['comment_by']
	cmt.content = doc['content']
	cmt.custom_is_system_generated = 1

	frappe.logger().debug(f"Current User: {frappe.session.user}, Roles: {frappe.get_roles()}")
	cmt.save()

	frappe.db.set_value("Comment", cmt.name, "owner", doc['comment_by'])
	frappe.db.commit()

@frappe.whitelist()
def set_status(doc):
	ticket = frappe.get_doc("Ticket Details", doc['client_ticket'])
	current_status = ticket.status
	new_status = doc['status']
	new_resolution = doc.get('resolution_details')

	# Case 1: Reopen → send resolution again → mark Resolved
	if current_status == "Reopen" and new_resolution:
		ticket.status = "Resolved"
		ticket.resolution_details = new_resolution

	# Case 2: Already Resolved/Closed → resolution updated → just update text
	elif current_status in ("Resolved", "Closed") and new_resolution:
		ticket.resolution_details = new_resolution

	# Case 3: Any other status update
	else:
		ticket.status = new_status
		if new_resolution:
			ticket.resolution_details = new_resolution

	ticket.save()
	frappe.db.commit()


@frappe.whitelist()
def set_resolution(doc):
	frappe.db.set_value("Ticket Details", doc['client_ticket'],"resolution_details", doc['resolution_details'])
	frappe.db.set_value("Ticket Details", doc['client_ticket'],"status", doc['status'])
	frappe.db.commit()

def upload_video_to_support(local_ticket_id):
	settings = frappe.get_cached_doc("Genie Settings")
	headers = {
		"Authorization": f"token {settings.get_password('support_api_token')}",
	}

	# Fetch file details from Frappe
	file_doc = frappe.get_all(
		"File", 
		filters={"attached_to_doctype": "Ticket Details", "attached_to_name": local_ticket_id},
		fields=["file_url", "file_name", "is_private"]
	)

	if not file_doc:
		return None

	file_record = file_doc[0]
	file_url = file_record["file_url"]  # Example: /files/screen-rec.mp4
	file_name = file_record["file_name"]
	is_private = file_record["is_private"]


	relative_path = file_url.lstrip("/")  # removes leading slash
	file_path = frappe.get_site_path(relative_path)
	# Determine the correct file path dynamically
	# if is_private:
	# 	# Private files are stored in /private/files/
	# 	file_path = frappe.get_site_path("private", "files", file_name)
	# else:
	# 	# Public files are stored in /public/files/
	# 	file_path = frappe.get_site_path("public", "files", file_name)


	# Read and upload file to support system
	with open(file_path, "rb") as f:
		files = {"file": (file_name, f, "video/mp4")}
		response = requests.post(
			f"{settings.support_url}/api/method/upload_file",
			headers=headers,
			files=files
		)

	# Get response from support system
	hd_ticket_file = response.json().get("message")
	return hd_ticket_file

@frappe.whitelist()
def create_ticket(title, description, category, screen_recording=None):
	settings = frappe.get_cached_doc("Genie Settings")
	headers = {
		"Authorization": f"token {settings.get_password('support_api_token')}",
	}
	local_ticket = create_local_ticket(title, description, category, screen_recording)     #### call fn to create local ticket

	hd_ticket_file = None
	hd_ticket_file = upload_video_to_support(local_ticket)

	user = frappe.session.user  # Default to the logged-in user
	userfullname = get_user_fullname(user)
	# Fetch API Key and Secret for the user
	user_doc = frappe.get_doc("User", "support@bizmap.in")
	api_key = user_doc.api_key
	api_secret = user_doc.get_password('api_secret')
	token = f'{api_key}:{api_secret}'
	doc = {	
				"description": description,
				"subject": title,
				"custom_created_byemail": f"{user}",
				"custom_created_byname": f"{userfullname}",
				"custom_category": f"{category}",
				"custom_reference_ticket_id": local_ticket,             ##### send local ticket id
				"custom_reference_ticket_token": token,
				"custom_client_url": f"{frappe.request.scheme}://{frappe.request.host}",
				**generate_ticket_details(settings),
			}
	hd_ticket = make_request(
		url=f"{settings.support_url}/api/method/supportsystem.supportsystem.custom.custom_api.custom_new",
		headers=headers,
		payload={
			"doc": doc,
			"attachments": [hd_ticket_file] if hd_ticket_file else [],
		}
	).get("message", {}).get("name")
	frappe.db.set_value("Ticket Details", local_ticket, "support_ticket_id", hd_ticket)
	return hd_ticket


def get_user_fullname(user: str) -> str:
	user_doctype = DocType("User")
	return (
		frappe.get_value(
			user_doctype,
			filters={"name": user},
			fieldname=Concat_ws(" ", user_doctype.first_name, user_doctype.last_name),
		)
		or ""
	)

def generate_ticket_details(settings):
	req_params = {}
	for row in settings.ticket_details:
		if row.type == "String":
			req_params[row.key] = row.value
		elif row.type == "Integer":
			req_params[row.key] = cint(row.value)
		elif row.type == "Context":
			req_params[row.key] = safe_eval(row.value, get_safe_globals(), {})
		else:
			req_params[row.key] = row.value

		if row.cast_to:
			if row.cast_to == "Int":
				req_params[row.key] = cint(req_params[row.key])
			elif row.cast_to == "String":
				req_params[row.key] = str(req_params[row.key])
			elif row.cast_to == "Float":
				req_params[row.key] = flt(req_params[row.key])

	return req_params

