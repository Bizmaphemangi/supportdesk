# Copyright (c) 2023, Wahni IT Solutions Pvt. Ltd. and contributors
# For license information, please see license.txt

import re
import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Concat_ws
from frappe.utils import cint, flt, get_url, now
from frappe.utils.safe_exec import get_safe_globals, safe_eval
import requests
from datetime import datetime
import json

# from genie.utils.requests import make_request


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
	cmt.comment_by = f"BizmapSupport ({doc['comment_by']})"
	cmt.content = doc['content'] + f"{doc['comment_by']} from Bizmap Support"
	cmt.custom_is_system_generated = 1
	cmt.save()
	frappe.log_error(f"Comment saved: {cmt.name}", "Comment Save Debug")
	frappe.db.set_value("Comment", cmt.name, "owner", doc['comment_by'])
	frappe.db.commit()

	# ticket = frappe.get_doc("Ticket Details", doc['client_ticket'])
	# recipient_user = ticket.owner

	# # Send real-time notification
	# frappe.publish_realtime(
	# 	event="eval_js",
	# 	message={
	# 		"message": f"You got a reply on Ticket: {ticket.name}"
	# 	},
	# 	user=recipient_user
	# )

	# # Create Notification Log
	# frappe.get_doc({
	# 	"doctype": "Notification Log",
	# 	"subject": f"New Reply on Ticket #{ticket.name} for {recipient_user}",
	# 	"for_user": recipient_user,
	# 	"document_type": "Ticket Details",
	# 	"document_name": ticket.name,
	# 	"from_user": doc['comment_by'],
	# 	"type": "Alert",
	# }).insert(ignore_permissions=True)

	# frappe.db.commit()

@frappe.whitelist()
def set_status(doc):
	frappe.log_error(f"{doc}")

	ticket = frappe.get_doc("Ticket Details", doc.get('client_ticket'))

	ticket.status = doc.get('status')
	if doc.get('resolution_details'):
		ticket.resolution_details = doc.get('resolution_details')

	ticket.save()


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

	# Determine the correct file path dynamically
	if is_private:
		# Private files are stored in /private/files/
		file_path = frappe.get_site_path("private", "files", file_name)
	else:
		# Public files are stored in /public/files/
		file_path = frappe.get_site_path("public", "files", file_name)


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
	response = requests.post(

	url=f"{settings.support_url}/api/method/supportsystem.supportsystem.custom.custom_api.custom_new",
	headers=headers,
    json={
        "doc": doc,
        "attachments": [hd_ticket_file] if hd_ticket_file else [],
    }
	)
	
	hd_ticket = response.json().get("message", {}).get("name")
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



@frappe.whitelist(allow_guest=True)
def make_timeline_entry(doc):
	ticket = frappe.get_doc("Ticket Details", doc.get('parent'))
	ticket.append("ticket_timeline", {
		"timestamp": datetime.now(),
		"date": doc.get('date'),
		"status": doc.get('status'),
		"notes": doc.get('notes'),
		"added_by": doc.get("added_by"),
	})
	ticket.save(ignore_permissions=True)

	return {"message": "Timeline entry synced successfully"}


@frappe.whitelist()
def sync_details_to_support(doc):
	doc = json.loads(doc)
	doc = {
			"custom_ticket_status": doc.get('status'),
			"custom_reference_ticket_id": doc.get('name'),
			'custom_rating': doc.get('rating') or '',
			'custom_feedback': doc.get("feedback_option") or '',
			'custom_feedback_extra': doc.get("feedback_extra") or '',
			'custom_category': doc.get("category") or ''
		}
	frappe.logger().info(f"[SyncDetails] Status: {doc.get('custom_ticket_status')}")

	settings = frappe.get_cached_doc("Genie Settings")

	payload = {'doc': doc}
	headers = {
		"Authorization": f"token {settings.get_password('support_api_token')}"
	}
	try:

		session = requests.Session()
		api_url = f"{settings.support_url}/api/method/supportsystem.supportsystem.custom.custom_hd_ticket.set_status"
		response = session.post(
			url=api_url,
			headers=headers,
			json=payload,
			timeout=30  # Set a timeout for the request
		)
		frappe.log_error(f"API Response: {response.status_code} - {response.text}", "API Response Debug")
	except requests.exceptions.RequestException as e:
		frappe.log_error(f"Error during API call: {str(e)}\nPayload: {payload}\nHeaders: {headers}", "API Error")
		frappe.throw("An error occurred while connecting to the support system.")


@frappe.whitelist()
def sync_timeline_to_support_system(doc):
	doc = json.loads(doc)
	settings = frappe.get_cached_doc("Genie Settings")

	idoc = frappe.get_doc("Ticket Details", doc.get('name'))

	if(idoc and doc.get('status') != idoc.status):
		try:
			timeline_entry = idoc.get('ticket_timeline')[-1] if idoc.get('ticket_timeline') else None
			if timeline_entry:
				headers = {
					"Authorization": f"token {settings.get_password('support_api_token')}"
				}
				url = f"{settings.support_url}/api/resource/Ticket Timeline Entry"
				data = {
					"parent": idoc.support_ticket_id,
					"parenttype": "Issue",
					"parentfield": "custom_ticket_timeline",
					"date": frappe.utils.today(),
					"status": doc.get('status'),
					"notes": timeline_entry.notes,
					"added_by": get_user_fullname(frappe.session.user)
				}
				response = requests.post(url, headers=headers, json=data)
				frappe.log_error(f"URL: {url}\nHEADERS: {headers}\nDATA: {data}\nResponse: {response}","PUT Data info")
		except Exception as e:
			frappe.log_error(f"timeline sync error:\n\n {str(e)}")


def auto_close_tickets():
	frappe.log_error("Auto-close job triggered")

	"""
	Automatically close tickets that have been Opened for more than X days (default 4).
	"""
	close_days = frappe.get_cached_value("Genie Settings", None, "close_ticket_after_days") or 4
	today = nowdate()
	cutoff_date = add_days(today, -close_days)

	tickets_to_close = frappe.db.get_all("Ticket Details", filters={
						"status": ["in", ["Open", "Re-Opened"]],
						"modified": ["<", cutoff_date]
					}, fields=["name", "modified"])

	for ticket in tickets_to_close:
		ticket_doc = frappe.get_doc("Ticket Details", ticket.name)
		ticket_doc.status = "Closed"
		ticket_doc.save(ignore_permissions=True)

	frappe.db.commit()