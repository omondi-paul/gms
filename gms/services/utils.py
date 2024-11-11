import frappe
import requests
import calendar
from datetime import datetime
from gms.services.login import login



@frappe.whitelist()
def send_sms(mobile, message):
    api_key = 'c9ade7e0c616b954c559efa86f00cfbb'
    partnerID = 7760
    sender_id = 'UPEOSOFT'
    endpoint_url = "https://sms.textsms.co.ke/api/services/sendsms/"

    payload = {
        "apikey": api_key,
        "partnerID": partnerID,
        "message": message,
        "shortcode": sender_id,
        "mobile": format_mobile_number(mobile)
    }

    try:
        response = requests.post(endpoint_url, json=payload)
        response = response.json()
        return response
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"{e}")
        return {'error': str(e)}, 400




def format_mobile_number(mobile):
    try:
        if mobile.isdigit() and len(mobile) >= 9:
            return "254" + mobile[-9:]
        else:
            return "Invalid mobile number."
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"{e}")
        return {'error': str(e)}, 400
    


def get_customer_balance(customer):
    customer_sql = f"""
        SELECT 
            SUM(debit) AS billed,
            SUM(debit - credit) AS unpaid
        FROM
            `tabGL Entry`
        WHERE
            party_type = 'Customer'
        AND
            party='{customer}'
        AND 
            is_cancelled = 0
    """

    billed_amount = frappe.db.sql(customer_sql, as_dict=True)

    unpaid_amount = billed_amount[0].get('unpaid') if billed_amount else 0

    return unpaid_amount


@frappe.whitelist(allow_guest=True)
def create_payment_entry(mode_of_payment, customer, amount, paid_to, reference_number, reference_date, payment_reference, pending_transaction):
    try:

        frappe.enqueue(
            create_payment_entry_job,
            queue="default",
            timeout=None,
            is_async=True,
            now=False,
            job_name=None,
            enqueue_after_commit=False,
            at_front=False,
            mode_of_payment=mode_of_payment,
            customer=customer,
            amount=amount,
            paid_to=paid_to,
            reference_number=reference_number,
            reference_date=reference_date,
            payment_reference=payment_reference,
            pending_transaction=pending_transaction
        )   

    except Exception as e:
        frappe.log_error(f"Error creating payment entry: {str(e)}")
        return {"status": "Error", "message": f"Failed to create payment entry: {str(e)}"}




def create_payment_entry_job(mode_of_payment, customer, amount, paid_to, reference_number, reference_date, payment_reference, pending_transaction):
    try:
        print(f"\n\n\n succcessssfulll \n\n\n")
        frappe.set_user('Administrator')

        payment_entry_data = {
                "doctype": "Payment Entry",
                "mode_of_payment": mode_of_payment,
                "party_type": "Customer",
                "payment_type": "Receive",
                "party": customer,
                "received_amount": amount,
                "paid_amount": amount,
                "target_exchange_rate": 1,
                "paid_to": paid_to,
                "reference_no": reference_number,
                "reference_date": reference_date,
                "paid_to_account_currency": "KES"
            }
        print(f"\n\n\n{payment_entry_data}\n\n\n")
        print(f"\n\n\n successfulll again \n\n\n")
            
        if payment_reference:
            payment_entry_data["references"] = payment_reference

        payment_entry = frappe.get_doc(payment_entry_data)
        payment_entry.insert(ignore_permissions=True, ignore_mandatory=True)
        if payment_entry.submit():
            existing_mpesa_payment_name = frappe.db.get_value(
                'Mpesa Payment Transactions', 
                {
                    'mpesa_receipt_number': reference_number
                },
                'name'
            )

            frappe.db.set_value('Mpesa Payment Transactions', existing_mpesa_payment_name, 'status', 'Reconciled')
            frappe.db.set_value('Pending Payment Transactions', pending_transaction, 'status', 'Reconciled')


        frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Error creating payment entry: {str(e)}")





