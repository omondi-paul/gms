import frappe
from frappe import _
from whatsapp_integration.service.rest import send_whatsapp_media, send_whatsapp_message


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


@frappe.whitelist(allow_guest=True)
def send_whatsapp_payment_link(invoice_name):
    try:
        doc = frappe.get_doc("Sales Invoice", invoice_name)
        member = frappe.get_all("Gym Member", {"full_name": doc.customer}, ["mobile_number"])
        if not member:
            frappe.throw(f"Gym Member not found for customer: {doc.customer}")

        BASE_URL = frappe.get_single("Gym URL").url
        phone = member[0].get("mobile_number")
        if not phone:
            frappe.throw(f"Mobile number not found for Gym Member: {doc.customer}")

        payment_link = f"{BASE_URL}/payment-requests/new?amount={doc.outstanding_amount}&mobile_number={phone}&sales_invoice={doc.name}"

        message = (f"Hello, {doc.customer}!\n\n"
                   f"Thank you for staying fit with us! You have an outstanding payment of {doc.outstanding_amount}. "
                   f"You can complete your payment using the following link: {payment_link}.\n\n"
                   f"Feel free to reach out if you have any questions. Stay healthy!")

        send_whatsapp_message(phone, message)
    except Exception as e:
        frappe.log_error(f"Error while sending WhatsApp payment link: {str(e)}")
        frappe.throw("Failed to send the payment link. Please try again later.")
