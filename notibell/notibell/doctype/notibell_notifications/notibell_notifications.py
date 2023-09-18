# Copyright (c) 2023, NestorBird and contributors
# For license information, please see license.txt

import frappe
import requests
import json
from frappe.model.document import Document

class NotiBellNotifications(Document):
	pass

@frappe.whitelist(allow_guest=True)
def send_push_notification(device_token, title, body, key, value):
    app_integration = frappe.get_doc("NotiBell Notifications")
    if not app_integration.enable_app_notifications:
        return {
            'statusCode': 404,
            'message': "Notification is not enable. Please enable it from App Integration"
        }
    if not app_integration.app_secret_key:
        return {
            'statusCode': 404,
            'message': "please Insert Secret Key in App Integration"
        }
    url = app_integration.url
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "key={app_secret_key}".format(app_secret_key=app_integration.app_secret_key),
    }
    payload = {
        "to": device_token,
        "collapse_key": "type_a",
        "notification": {
            "body": "" + body,
            "title": "" + title,
        },
        "data": {
            "key": key,
            "value": value
        }
    }
    payload = json.dumps(payload)
    response = requests.request("POST", url, headers=headers, data=payload)
    return response
