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

SOCAIL_MEDIA_PLATEFORM = {
    "1":"Google",
    "2":"Apple"
}
@frappe.whitelist(allow_guest=True)
def sign_up():

    try :
        if frappe.local.request.method != "POST":
            return "Only Post API"
        
        frappe.local.request
        body =  frappe.local.form_dict
        frappe.local.response.data
    except Exception as  e :
        print (e)
    
    if is_signup_disabled():
        frappe.throw(_("Sign Up is disabled"), title=_("Not Allowed"))

    user = frappe.db.get("User", {"email": body.get("email")})
    user_count = frappe.db.sql("""SELECT COUNT(*) from `tabUser` WHERE email = '{email}' OR mobile_no = '{mobile_no}'""".format(
        email=body.get("email"),
        mobile_no=body.get("phone_no") 
        ))[0][0]

    if user_count > 0:
        return {
            'status_code': 200,
            'message': 'User already exists with this email or phone number'
        }
    else:
        if frappe.db.get_creation_count("User", 60) > 300:
            frappe.respond_as_web_page(
                _("Temporarily Disabled"),
                _("Too many users signed up recently, so the registration is disabled. Please try back in an hour"),
                http_status_code=429,
            )

        user = frappe.new_doc("User")
        user.update({
            "email": body.get("email"),
            "first_name": body.get("first_name"),
            "last_name": body.get("last_name"),
            "full_name": body.get("escape_html(full_name)"),
            "gender": body.get("gender"),
            "birth_date": body.get("birth_date"),
            "enabled": 1,
            "new_password": body.get("new_password " if "new_password " else random_string(10)),
            "user_type": "System User",
            "role_profile_name": "notibell role profile"
        })

        is_table_already_exists = 0
        if body.get("social_media_platform"):
            if body.get("social_media_guid"):
                if user.get("social_logins"):
                    for media in user.get("social_logins"):
                        if media.provider==SOCAIL_MEDIA_PLATEFORM[body.get("social_media_platform")]:
                            media.userid= body.get("social_media_guid")
                            is_table_already_exists=1
                if  not is_table_already_exists:
                    user.append("social_logins", {
                        "provider": SOCAIL_MEDIA_PLATEFORM[body.get("social_media_platform")],
                        "userid": body.get("social_media_guid")
                    })
                    user.is_social_login = 1
                    user.is_verified = 1
                    user.new_password = "Qwerty@1234"
                    user.flags.ignore_permissions = True
                    user.flags.ignore_password_policy = True
                    user.send_welcome_email = False
                    user.save()
                    create_employee(user, doc=None)
                    response = {
                        "is_social_login": 1,
                        "is_verified": 1
                    }

                    return {"status_code": 200, "message": "User signup successful", "response": response}
                else:
                    return {"status_code": 400, "message": "Please provide the social media GUID"}
            else:
                return {"status_code": 400, "message": "Please provide the social media GUID"}
        else:
            user.flags.ignore_permissions = True
            user.flags.ignore_password_policy = True
            user.insert()
            create_employee(user, doc=None)
            default_role = frappe.db.get_single_value("Portal Settings", "default_role")

            if default_role:
                user.add_roles(default_role)

            if user.flags.email_sent:
                return {
                    'status_code': 200,
                    'message': 'User registered successfully'
                }
            else:
                return {"status_code": 2, "message": _("Please ask your administrator to verify your sign-up")}


def create_employee(user, doc):
    try:
 
        employee = frappe.new_doc('Employee')
        employee.update({
            "full_name": user.full_name,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_of_birth": user.birth_date,
            "gender": user.gender,
            "date_of_joining": frappe.utils.now_datetime(),
            "user_id": user.email,
            "company_email": user.email
            
          
        })
        employee.flags.ignore_mandatory = True
        employee.insert(ignore_permissions=True)

        print(f"Employee {employee.employee_name} created successfully.")

    except Exception as e:
        print(f"Error creating employee: {str(e)}")




# Function to generate OTP with timestamp
def resend_otp(email=None, type=None, length=6, phone_no=None):
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

# Function to handle OTP for Signup and Forgot scenarios
@frappe.whitelist(allow_guest=True)
def otp():
    try:
        if frappe.local.request.method != "POST":
            return "Only Post API"
        body = frappe.local.request
        frappe.local.response.data
    except Exception as e:
        # Log the exception for better debugging
        frappe.log_error(f"Error in OTP function: {e}")
        return "An error occurred while processing your request."

    otp_type = body.get("type")

    if otp_type == "Signup":
        user_exists = frappe.db.exists("User", {"email": body.get("email")})
        if user_exists:
            return "Email already exists. Choose another email for sign-up."

    elif otp_type == "Forgot":
        user_exists = frappe.db.exists("User", {"email": body.get("email")})
        if not user_exists:
            return "Email not found. Enter a valid email for password recovery."

    resend_time = timedelta(minutes=2)
    last_otp_entry = frappe.get_all(
        "OTP Log",
        filters={"email": body.get("email"), "type": otp_type},
        fields=["name", "time"],
        order_by="creation DESC",
        limit=1
    )

    if last_otp_entry and datetime.now() - last_otp_entry[0]["time"] < resend_time:
        return "OTP already sent. Please wait before requesting again."

    otp, time = resend_otp(email=body.get("email"), type=otp_type)
    send_otp(body.get("email"), otp)

    return {
        "message": "OTP has been sent to your email account",
        "otp": otp,
        "type": otp_type,
        "email": body.get("email")
    }

# Function to verify OTP and set a new password
@frappe.whitelist(allow_guest=True)
def verify_otp():
    try:
        if frappe.local.request.method != "POST":
            return "Only Post API"
        body = frappe.local.request
        frappe.local.response.data
    except Exception as e:
        frappe.log_error(f"Error in verify_otp function: {e}")
        return "An error occurred while processing your request."

    otp_type = body.get("type")

    # Check if required fields are present based on otp_type
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

            return "Password successfully updated."
        elif otp_type == "Signup":
            return "Signup verification successful."
        else:
            return "Invalid request type."
    else:
        return "Invalid OTP. Please try again."









#no need to
@frappe.whitelist(allow_guest=True)
def login(email=None, password=None, social_media_guid=None, social_media_platform=None):
    try:
        if email and password:
            # Email/password login
            user = frappe.get_doc("User", {"email": email})
            if user and user.check_password(password):
                return {
                    'status_code': 200,
                    'message': 'Email/password login successful',
                    'user_id': user.name
                }
            else:
                return {
                    'status_code': 401,
                    'message': 'Invalid email/password'
                }
        elif social_media_guid and social_media_platform:
            # Social media login
            user = frappe.get_doc({
                "doctype": "User",
                "social_logins": [{
                    "provider": SOCAIL_MEDIA_PLATEFORM.get(social_media_platform),
                    "userid": social_media_guid
                }]
            })

            if user:
                return {
                    'status_code': 200,
                    'message': 'Social media login successful',
                    'user_id': user.name
                }
            else:
                return {
                    'status_code': 401,
                    'message': 'Invalid social media login credentials'
                }
        else:
            return {
                'status_code': 400,
                'message': 'Invalid request. Provide email/password or social media login credentials.'
            }

    except Exception as e:
        print(f"Error during login: {str(e)}")
        return {
            'status_code': 500,
            'message': 'Internal server error during login'
        }