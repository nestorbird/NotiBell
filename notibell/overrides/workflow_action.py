import frappe
import random
from frappe import _
from frappe.model.document import Document

from frappe.workflow.doctype.workflow_action.workflow_action import update_completed_workflow_actions_using_role
from frappe.workflow.doctype.workflow_action.workflow_action import get_permission_query_conditions

def update_completed_workflow_actions_using_role_custom(user=None, workflow_action=None):
    user = user if user else frappe.session.user
    if not workflow_action:
        return
    workflow_action_doc = frappe.get_doc("Workflow Action", workflow_action[0].name)
    workflow_action_doc.status = "Completed"
    workflow_action_doc.completed_by = user
    workflow_action_doc.completed_by_role = workflow_action[0].role
    workflow_action_doc.save(ignore_permissions=True)


def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user

	if user == "Administrator":
		return ""
	else:
		return ""