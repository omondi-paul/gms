import frappe
from frappe import _
from whatsapp_integration.service.rest import send_whatsapp_media


def send_whatsapp_job(mobile_number, invoice_number):
    try:
        send_invoice_whatsapp(mobile_number, invoice_number)
    except Exception as e:
        frappe.log_error(f"Failed to send WhatsApp message for invoice {invoice_number} to {mobile_number}: {str(e)}", "WhatsApp Notification Error")

@frappe.whitelist(allow_guest=True)
def send_invoice_whatsapp(mobile_number, invoice_name):
    whatsapp_url = frappe.get_single("Gym URL").url
    member_name = frappe.db.get_value("Gym Member", {"mobile_number": mobile_number}, ['full_name'])
    payment_type = frappe.db.get_value('Sales Invoice', invoice_name, 'custom_payment_type')
    media_url = f"{whatsapp_url}/api/method/frappe.utils.print_format.download_pdf?doctype=Sales%20Invoice&name={invoice_name}&format=Sales%20Invoice&no_letterhead=0&letterhead=Invoice%20LH&settings=%7B%7D&_lang=en"
    msg = (f"Hey there, {member_name}!\n\nThis is your sales invoice. "
           f"Be sure to press 'Pay' to redirect to the payment link and complete your {payment_type}.\n\n"
           f"Thank you for choosing our services and staying fit with us!")
    
    try:
        res = send_whatsapp_media(to_number=mobile_number, message=msg, media_url=media_url)
        if "error" in res:
            frappe.log_error(f"WhatsApp media send error: {res['error']}", "WhatsApp Media Send Error")
        return res
    except Exception as e:
        frappe.log_error(f"Unexpected error in sending WhatsApp message: {str(e)}", "WhatsApp Media Send Error")
        return {"error": str(e)}




