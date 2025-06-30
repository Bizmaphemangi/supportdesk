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
		# previous_status = frappe.db.get_value(self.doctype, self.name, "status")
		# current_status = self.status

		# if previous_status != current_status and current_status == "Resolved":
		# 	notification_log = frappe.get_doc({
		# 		"doctype": "Notification Log",
		# 		"subject": "Your Ticket has been Resolved",
		# 		"for_user": self.owner,
		# 		"document_type": self.doctype,
		# 		"document_name": self.name,
		# 		"type": "Alert"
		# 	})
		# 	notification_log.insert(ignore_permissions=True)
		# 	frappe.db.commit()
		# 	frappe.db.set_value("Notification Log", notification_log.name, "owner", notification_log.for_user)
		# 	frappe.db.commit()
			
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