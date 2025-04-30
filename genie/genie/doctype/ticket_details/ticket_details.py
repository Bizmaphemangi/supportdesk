import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Concat_ws
from frappe.utils import today
from genie.utils.requests import make_request
import requests
import frappe
from frappe.model.document import Document
from requests.adapters import HTTPAdapter

class TicketDetails(Document):
	def validate(self):
		if self.status == 'Closed':
			doc = {
				"status": self.status,
				"custom_reference_ticket_id": self.name,
				'feedback_option': self.feedback_option or '',
				'feedback_extra': self.feedback_extra or ''
			}
		elif self.status == 'Re-Opened':
			doc = {
				"status": self.status,
				"custom_reference_ticket_id": self.name
			}
		elif self.status == 'Replied':
			self.responded_on = frappe.utils.now_datetime()
			return
		else:
			return

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
				json=payload
			)
			response.raise_for_status()

			# Log the full response for debugging
			frappe.log_error(f"API Response: {response.status_code} - {response.text}", "API Response Debug")
			return response.json()
		except requests.exceptions.RequestException as e:
			frappe.log_error(f"Error during API call: {str(e)}\nPayload: {payload}\nHeaders: {headers}", "API Error")
			frappe.throw("An error occurred while connecting to the support system.")

	def on_update(self):
		previous = self.get_doc_before_save()
		if not self.ticket_timeline:
			self.append("ticket_timeline", {
				"timestamp": frappe.utils.now_datetime().isoformat(),
				"date" : today(),
				"status": self.status,
				"note": "Ticket created",
				"added_by": get_user_fullname(frappe.session.user)
			})
			self.save()	
			timeline_entry = self.ticket_timeline[-1] 

		elif previous and self.status != previous.status and self.status in ('Closed', 'Re-Opened'): 
			self.append("ticket_timeline", {
				"timestamp": frappe.utils.now_datetime().isoformat(),
				"date": today(),
				"status": self.status,
				"note": f"Status changed from {previous.status} to {self.status}",
				"added_by": get_user_fullname(frappe.session.user)
			})
			self.save()
			timeline_entry = self.ticket_timeline[-1] 
			self.sync_timeline_to_support_system(timeline_entry)
		
		else: return


	def sync_timeline_to_support_system(self,timeline_entry):
		session = requests.Session()
		try:
			settings = frappe.get_cached_doc("Genie Settings")
			support_url = f"{settings.support_url}/api/method/supportsystem.supportsystem.custom.custom_hd_ticket.make_timeline_entry"
			headers = {
				"Authorization": f"token {settings.get_password('support_api_token')}"
			}
			data = {
				"doctype": "Ticket Timeline Entry",
				"timestamp": timeline_entry.timestamp,   
				"date":today(),
				"status": timeline_entry.status,
				"note": timeline_entry.note,
				"added_by": timeline_entry.added_by,
				"parent": self.support_ticket_id,  # Should match support-side ticket name
				"parenttype": "HD Ticket",
				"parentfield": "ticket_timeline"
			}
			response = session.post(support_url, headers=headers, json=data)
			response.raise_for_status()  # Will raise HTTPError for bad responses

		except Exception as e:
			frappe.log_error(f"Timeline sync error: {str(e)}")
			
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