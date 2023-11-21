import frappe 
import random
from frappe import _
from frappe.model.document import Document
from datetime import datetime, timedelta
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
        return permitted_action
    except Exception as e:
        print(e)




from frappe.website.utils import is_signup_disabled
import frappe.permissions
from frappe.utils import (escape_html)
from frappe.utils import escape_html, random_string
import frappe
from frappe import _

# Function to generate OTP with timestamp
def resend_otp(email, type, length=6, phone_no=None):
    otp_value = random.randint(10**(length-1), (10**length)-1)
    otp_value = otp_value % 10000
    time = frappe.utils.now()

    frappe.msgprint(f"DEBUG: type={type}")  # For debugging

    # Create and insert OTP Log document
    otp_log = frappe.get_doc({
        "doctype": "OTP Log",
        "otp": otp_value,
        "email": email,
        "time": time,
        "phone_no": phone_no,
        "type": type
    })

    try:
        otp_log.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Error inserting OTP Log: {str(e)}")
        return "Error saving OTP Log."

    return otp_value, time

# Function to send OTP via email
def send_otp(email, otp):
    frappe.sendmail(
        recipients=[email],
        subject="OTP Confirmation",
        message=f"Your OTP is: {otp}",
        delayed=False,
        header=["OTP Confirmation", "orange"]
    )
    frappe.clear_messages()
    
    
    
    
    

# Constants
SIGNUP_OTP_TYPE = "Signup"
FORGOT_OTP_TYPE = "Forgot"

# Function to handle OTP for Signup and Forgot scenarios
@frappe.whitelist(allow_guest=True)
def otp():
    try:
        if frappe.local.request.method != "POST":
            return {
                'status_code': 405,
                'message': 'Only POST requests are allowed'
            }
        body = frappe.local.form_dict
        email = body.get("email")
        otp_type = body.get("type")

        # Check if 'email' and 'type' are present in the request
        if not email or not otp_type:
            return {
                'status_code': 400,
                'message': 'Email and OTP type are required in the request'
            }
        if otp_type == SIGNUP_OTP_TYPE and frappe.db.exists("User", {"email": email}):
            return {
                "status_code": 409,
                "message": "Email already exists. Choose another email for sign-up."
            }

        elif otp_type == FORGOT_OTP_TYPE and not frappe.db.exists("User", {"email": email}):
            return {
                "status_code": 404,
                "message": "Email not found. Enter a valid email for password recovery."
            }

        resend_time = timedelta(minutes=2)
        print("toxic", resend_time)
        last_otp_entry = frappe.get_all(
            "OTP Log",
            filters={"email": email, "type": otp_type},
            fields=["name", "time"],
            order_by="creation DESC",
            limit=1
        )
        if last_otp_entry and datetime.now() - last_otp_entry[0]["time"] < resend_time:
            return {
                'status_code': 429,
                'message': 'OTP already sent. Please wait before requesting again.'
                }

        otp, time = resend_otp(email=email, type=otp_type)
        send_otp(email, otp)

        return {
            "status_code": 200,
            "message": "OTP has been sent to your email account",
            "otp": otp,
            "type": otp_type,
            "email": email
        }

    except Exception as e:
        # Log the exception for better debugging
        frappe.log_error(f"Error in OTP function: {e}", title="OTP Function Error")
        return {
            'status_code': 500,
            'message': 'An error occurred while processing your request.'
        }




# Function to verify OTP and set a new password
@frappe.whitelist(allow_guest=True)
def verify_otp():
    try:
        # Check if the request method is POST
        if frappe.local.request.method != "POST":
            return "Only POST requests are allowed."

        # Get the request body
        body = frappe.local.form_dict

        # Validate the request body
        if not body:
            return "Request body is empty."

        otp_type = body.get("type")

        if otp_type == "Signup":
            required_fields = ["email", "otp", "type"]
        elif otp_type == "Forgot":
            required_fields = ["email", "new_password", "otp", "type"]
        else:
            return "Invalid request type."

        if not all(body.get(field) for field in required_fields):
            return f"Required fields ({', '.join(required_fields)}) are missing for verification."

        # Get the latest OTP entry for the given email and type
        otp_entry = frappe.get_all(
            "OTP Log",
            filters={"email": body.get("email"), "type": otp_type},
            fields=["name", "otp"],
            order_by="creation DESC",
            limit=1
        )

        if otp_entry and otp_entry[0]["otp"] == body.get("otp"):
            if otp_type == "Forgot":
                # Only update the password if the type is "Forgot"
                user = frappe.get_doc("User", {"email": body.get("email")})
                user.set("new_password", body.get("new_password"))
                user.save(ignore_permissions=True)
                frappe.db.commit()

                return {
                    "status_code": 200,
                    "message": "Password successfully updated."
                }
            elif otp_type == "Signup":
                return "Signup verification successful."
            else:
                return "Invalid request type."
        else:
            return "Invalid OTP. Please try again."

    except Exception as e:
        frappe.log_error(f"Error in verify_otp function: {e}")
        return "An error occurred while processing your request."



