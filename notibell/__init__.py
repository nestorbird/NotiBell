
__version__ = '0.0.1'

from frappe import api
from frappe.workflow.doctype.workflow_action import workflow_action

from notibell.overrides.workflow_action import update_completed_workflow_actions_using_role_custom


# get_workflow_action_by_role = custom_get_workflow_action_by_role
workflow_action.update_completed_workflow_actions_using_role=update_completed_workflow_actions_using_role_custom

# overriding permission query
from notibell.overrides.workflow_action import get_permission_query_conditions
workflow_action.get_permission_query_conditions=get_permission_query_conditions


# Customized Watcherp Functions
from notibell.overrides.api import handle

# monkey-patching
api.handle = handle


