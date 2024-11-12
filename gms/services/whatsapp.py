import frappe
from frappe import _
from datetime import datetime, timedelta, date
import urllib.parse
from frappe.utils import today, date_diff, getdate
import random
from whatsapp_integration.service.rest import send_whatsapp_media, send_whatsapp_message
from frappe.utils.file_manager import save_file
from frappe.utils.pdf import get_pdf
from frappe.utils import get_url
import calendar

def whatsapp_integration():
    pass




def send_whatsapp_job(mobile_number, invoice_number):
    try:
        send_invoice_whatsapp(mobile_number, invoice_number)
    except Exception as e:
        frappe.log_error(f"Failed to send WhatsApp message for invoice {invoice_number} to {mobile_number}: {str(e)}", "WhatsApp Notification Error")


    



@frappe.whitelist(allow_guest=True)
def send_invoice_whatsapp( mobile_number, invoice_name):
    member_name = frappe.db.get_value("Gym Member", {"mobile_number": mobile_number}, ['full_name'])

    payment_type = frappe.db.get_value('Sales Invoice', invoice_name, 'custom_payment_type')

    media_url = f"{get_url()}/api/method/frappe.utils.print_format.download_pdf?doctype=Sales%20Invoice&name={invoice_name}&format=Chama%20Invoice&no_letterhead=0&letterhead=Chamaa%20Invoice%20LH"

    msg = f"Hello {member_name},\n\n kindly remember to remit your {payment_type} payment on time. \n\n Thank you."

    try:
        res = send_whatsapp_media(to_number=mobile_number, message=msg, media_url=media_url)
        if "error" in res:
            frappe.log_error(f"WhatsApp media send error: {res['error']}", "WhatsApp Media Send Error")
        return res
    except Exception as e:
        frappe.log_error(f"Unexpected error in sending WhatsApp message: {str(e)}", "WhatsApp Media Send Error")
        return {"error": str(e)}


