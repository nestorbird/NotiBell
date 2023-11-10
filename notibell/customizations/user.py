from termios import CINTR
import frappe
import random
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils.data import cint
from frappe.utils.password import check_password, get_password_reset_limit, update_password
from frappe.core.doctype.user.user import User
import requests
from frappe.handler import uploadfile

from frappe.core.doctype.user.user import rate_limit




@frappe.whitelist(allow_guest=True)
def otp(type=None, email=None, mobile=None):
    if type == "Signup":
        if frappe.db.exists("User", {"email": email}):
            return "This User Already Exists!"
        else:
            otp = generate_otp(email=email)
            send_otp(email, otp)
            return {
                "message": "OTP has been sent to your email account or mobile number",
                "otp": otp,
                "email": email
            }
    elif type == "Forgot":
        if frappe.db.exists("User", {"email": email}):
            user = frappe.get_doc("User", {"email": email})
            otp = generate_otp(email=email)
            user.recent_otp = otp
            user.save(ignore_permissions=True)
            send_otp(email, otp)
            return {
                "message": "OTP has been sent to your email account or mobile number",
                "otp": otp,
                "email": email
            }
        else:
            return "User not found!"
    else:
        return "Invalid request type"


def generate_otp(email=None, length=6):
    otp_value = random.randint(10**(length-1), (10**length)-1)
    otp_value = otp_value % 10000
    time = frappe.utils.now()
    
    otp_log = frappe.get_doc({
        "doctype": "OTP Log",
        "otp": otp_value,
        "email": email,
        "time": time,
    })
    otp_log.insert(ignore_permissions=True)

    return otp_value


def send_otp(email, otp):
    frappe.sendmail(
        recipients=[email],
        subject="OTP Confirmation",
        message="Your OTP is: {}".format(otp),
        delayed=False,
        header=["OTP Confirmation", "orange"]
    )
    frappe.clear_messages()
