import frappe
from notibell.overrides.handler import custom_uploadfile

def validate(doc,method):
    if doc.get("user_image_file"):
        form_data = {
				"doctype" : "Employee",
				"filedata":doc.get("user_image_file"),
				"filename" :doc.name+"_user_image.png",
				"docname":doc.name,
				"filedata":doc.get("user_image_file")
			}
        url = custom_uploadfile(form_data=form_data)
        doc.custom_face_registration = url