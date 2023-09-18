import frappe
from frappe import _, is_whitelisted

@frappe.whitelist()
def custom_uploadfile(form_data = None):
	ret = None
	try:
		if frappe.form_dict.get("from_form"):
			try:
				ret = frappe.get_doc(
					{
						"doctype": "File",
						"attached_to_name": frappe.form_dict.docname,
						"attached_to_doctype": frappe.form_dict.doctype,
						"attached_to_field": frappe.form_dict.docfield,
						"file_url": frappe.form_dict.file_url,
						"file_name": frappe.form_dict.filename,
						"is_private": frappe.utils.cint(frappe.form_dict.is_private),
						"content": frappe.form_dict.filedata,
						"decode": True,
					}
				)
				ret.save()
		
			except frappe.DuplicateEntryError:
				ret = None
				frappe.db.rollback()
		# When We are Uploading image from front end , then we will call upload file function and pass the form_data in it 
		elif form_data:
			ret = frappe.get_doc(
				{
					"doctype": "File",
					"attached_to_name":form_data.get("docname"),
					"attached_to_doctype": form_data.get("doctype"),
					"file_url": "",
					"file_name": form_data.get("filename"),
					"is_private": 0,
					"content": form_data.get("filedata"),
					"decode": True,
				}
			)
			ret.save()
			return ret.file_url
			
			
		else:
			if frappe.form_dict.get("method"):
				method = frappe.get_attr(frappe.form_dict.method)
				is_whitelisted(method)
				ret = method()
	except Exception:
		frappe.errprint(frappe.utils.get_traceback())
		frappe.response["http_status_code"] = 500
		ret = None

	return ret