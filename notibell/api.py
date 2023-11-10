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

            if doc_entry.docstatus == 1 or doc_entry.docstatus == 2:
                continue

            if entry["reference_doctype"] == "Leave Application" and not doc_entry.leave_approver == user:
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

            mod_user = frappe.get_doc("User", entry["modified_by"]).full_name
            permitted_action[j]["full_name"] = mod_user

            permitted_action[j]["logged_user"] = user_details[0]["full_name"]

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



from frappe.website.utils import is_signup_disabled
from datetime import timedelta
from urllib import response
import frappe
import frappe.defaults
import frappe.permissions
import frappe.share
from frappe import STANDARD_USERS, _, msgprint, throw
from frappe.core.doctype.user_type.user_type import user_linked_with_permission_on_doctype
from frappe.desk.doctype.notification_settings.notification_settings import (
	create_notification_settings,
	toggle_notifications,
)
from frappe.desk.notifications import clear_notifications
from frappe.model.document import Document
from frappe.query_builder import DocType
from frappe.rate_limiter import rate_limit
from frappe.utils import (
	cint,
	escape_html,
	flt,
	format_datetime,
	get_formatted_email,
	get_system_timezone,
	has_gravatar,
	now_datetime,
	today,
)
from frappe.utils.deprecations import deprecated
from frappe.utils.password import check_password, get_password_reset_limit
from frappe.utils.password import update_password as _update_password
from frappe.utils.user import get_system_managers
from frappe.utils import escape_html, random_string
import frappe
from frappe import _
from frappe.utils import escape_html, random_string

@frappe.whitelist(allow_guest=True)
def sign_up(email, full_name, first_name, last_name, gender, birth_date,phone_no=None, new_password=None):
    print(email, full_name, first_name, last_name, gender, birth_date)
    if is_signup_disabled():
        frappe.throw(_("Sign Up is disabled"), title=_("Not Allowed"))

    user = frappe.db.get("User", {"email": email})
    user = frappe.db.sql("""SELECT COUNT(*) from `tabUser` WHERE email = '{email}' OR mobile_no = '{mobile_no}'""".format(
    email = email,
    mobile_no = phone_no
    ))
    if user[0][0] > 0:
        return {
            'status_code': 200,
            'message': 'User already exist with this email or phone number'
            }
    else:
        if frappe.db.get_creation_count("User", 60) > 300:
            frappe.respond_as_web_page(
                _("Temporarily Disabled"),
                _(
                    "Too many users signed up recently, so the registration is disabled. Please try back in an hour"
                ),
                http_status_code=429,
            )

        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "full_name": escape_html(full_name),
                "gender": gender,
                "birth_date": birth_date,
                "enabled": 1,
                "new_password": new_password if new_password else random_string(10),
                "user_type": "System User",
                "role_profile_name": "notibell role profile"
            }
        )

        user.flags.ignore_permissions = True
        user.flags.ignore_password_policy = True
        user.insert()
        create_employe(user, doc=None)
        default_role = frappe.db.get_single_value("Portal Settings", "default_role")
        if default_role:
            user.add_roles(default_role)

       
        if user.flags.email_sent:
            return {
        'status_code': 200,
        'message': 'User registered successfully'
    }
        else:
            return 2, _("Please ask your administrator to verify your sign-up")


def create_employe(user, doc):
    print(user)
    employee = frappe.new_doc('Employee')

    employee.full_name = user.full_name
    employee.first_name = user.first_name
    employee.last_name = user.last_name
    employee.date_of_birth = user.birth_date
    employee.gender = user.gender
    employee.date_of_joining = frappe.utils.now_datetime()
    employee.user_id = user.email

    employee.flags.ignore_mandatory = True
    employee.insert(ignore_permissions=True)



