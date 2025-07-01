from supportdesk.setup.file import create_supportdesk_folder
import frappe

def after_install():
    create_supportdesk_folder()
    create_support_user()
    create_supportdesk_role()


def create_supportdesk_role():
    # Check if the role already exists
    if not frappe.db.exists("Role", "support"):
        try:
            # Create the Genie Manager role
            role = frappe.get_doc({
                "doctype": "Role",
                "role_name": "Support",
                "description": "Role for SupportDesk App Users",
            })
            role.insert(ignore_permissions=True)
            frappe.db.commit()
            frappe.msgprint(("Role 'Support' has been created."))
        except Exception as e:
            frappe.msgprint(("Error creating role: {0}").format(str(e)))
            frappe.log_error(frappe.get_traceback(), "Error Creating Role - Genie Manager")
    else:
        frappe.msgprint(("Role 'Support' already exists."))



def create_support_user():
    if not frappe.db.exists("User", "support@bizmap.in"):
        # Create a new user
        user = frappe.get_doc({
            "doctype": "User",
            "email": "support@bizmap.in",
            "first_name": "BizmapSupport",
            "enabled": 1,
            "roles": [{"role": "System Manager"}],  # Assign desired roles
        })
        user.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.msgprint("Default user 'BizmapSupport' has been created.")
    else:
        frappe.msgprint("User 'BizmapSupport' already exists.")