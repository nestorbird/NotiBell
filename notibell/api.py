import frappe 
import random
from frappe import _
from frappe.model.document import Document

import frappe.exceptions

# @frappe.whitelist(allow_guest=True)
@frappe.whitelist()
def action_list():
    try:
        if frappe.local.request.method != "GET":
            return "Only GET API"
        args = frappe.local.request.args
        if args.get("pagination"):
            pagination = args.get("pagination")
        
        # get only permitted workflow action
        action_list = permitted_workflow_action()

        frappe.local.response.data = action_list
    except Exception as e:
        print(e)

# get only permitted workflow action
def permitted_workflow_action():
    try:
        action_list = frappe.db.get_all("Workflow Action", 
        fields=["name", "reference_doctype", "reference_name", "modified_by", "discard"],
        filters=[{"status":"Open"},{"discard": "No"}],
        limit_page_length = "*")
        user = frappe.session.user
        permitted_action = []
        
        i = -1
        for entry in action_list:
            i = i + 1
            doc_entry = frappe.get_doc(entry["reference_doctype"], entry["reference_name"])
            
            if not doc_entry.has_permission("write"):
                continue

            permitted_action.append(action_list[i])
            j = len(permitted_action) - 1
            permitted_action[j]["current_state"] = doc_entry.workflow_state
            
            user_detail_qry = f"""SELECT
                    US.full_name,
                    RO.role
                FROM
                    `tabUser` US
                JOIN 
                    `tabHas Role` RO ON US.name = RO.parent
                WHERE
                    US.name = "{user}"; """
            user_details = frappe.db.sql(user_detail_qry, as_dict=True)
            role = set()
            for dt in user_details:
                role.add(dt["role"])
            permitted_action[j]["roles"] = role
            permitted_action[j]["full_name"] = user_details[0]["full_name"]

            workflow_trasition_qry = f"""SELECT
                    WT.next_state as next_state,
                    WT.action,
                    WT.allowed as role_allowed,
                    WT.state as current_state
                FROM
                    `tabWorkflow Transition` WT
                JOIN 
                    `tabWorkflow` WF ON WF.name = WT.parent
                WHERE
                    WF.is_active = 1
                    AND WF.document_type = "{entry["reference_doctype"]}"
                    AND WT.allowed in ({', '.join(f'"{element}"' for element in permitted_action[j]["roles"])})
                    AND WT.state = "{doc_entry.workflow_state}"; """

            workflow_transition = frappe.db.sql(workflow_trasition_qry, as_dict=True)

            permitted_action[j]["workflow_transition"] = workflow_transition

        # frappe.db.sql(workflow_trasition_qry)
        return permitted_action
    except Exception as e:
        print(e)
