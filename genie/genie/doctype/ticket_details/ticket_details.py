import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Concat_ws
from frappe.utils import today
from genie.utils.requests import make_request
import requests
import frappe
from frappe.model.document import Document
from requests.adapters import HTTPAdapter
import pytz

class TicketDetails(Document):
	def validate(self):
		pass		
		
	def on_update(self):
		
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