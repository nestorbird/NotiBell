import frappe
from notibell.notibell.doctype.notibell_notifications.notibell_notifications import send_push_notification



# def validate(doc, method=None):
#     if doc.doctype == "Workflow Action":
#         reference = doc.reference_name
#         reference_doctype = doc.reference_doctype
#         permitted_roles = doc.permitted_roles
#         for role in permitted_roles:
#             role_name = role.get("role")
#             if role_name:
#                 users_with_role = frappe.get_all("User", filters={"role": role_name}, fields=["name"])
#                 for user in users_with_role:
#                     device_token=frappe.db.get_list("Push Notification",filters={"user":user.name},fields=["device_token"],pluck='device_token')
#                     for device_token in device_token:
#                         title = "New Workflow Action"
#                         body = f"A new {reference_doctype} '{reference}' requires your approval."
#                         key = "workflow_action"
#                         value = {
#                             "reference_doctype": reference_doctype,
#                             "reference_name": reference
#                         }
#                         send_push_notification(device_token, title, body, key, value)

@frappe.whitelist(allow_guest=True)
def validate(doc, method=None):
    if doc.doctype == "Workflow Action" and doc.status=="Open":
        reference = doc.reference_name
        reference_doctype = doc.reference_doctype
        permitted_roles = doc.permitted_roles
        previous_workflow_action = doc.name
        next_permitted_roles = [role.get("role") for role in permitted_roles]    
        if next_permitted_roles:
            for role_name in next_permitted_roles:
                push_notifications(role_name, reference_doctype, reference)


def push_notifications(role_name, reference_doctype, reference):
    users_with_role = frappe.get_all("User", filters={"role": role_name}, fields=["name"])  
    for user in users_with_role:
            device_token=frappe.db.get_value("Push Notifications",{"user":user.name},"device_token")
            # device_tokens_list = frappe.db.get_list("Push Notification", filters={"user": user.name}, fields=["device_token"], pluck='device_token')
            # for device_token in device_tokens_list:
            title = "New Workflow Action"
            body = f"A new {reference_doctype} '{reference}' requires your approval."
            key = "workflow_action"
            value = {
                "reference_doctype": reference_doctype,
                "reference_name": reference
            }
            send_push_notification(device_token, title, body, key, value)
    
