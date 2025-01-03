import frappe
import requests
import os
from dotenv import load_dotenv
from gms.services.utils import format_mobile_number
from gms.services.utils import create_payment_entry
from gms.services.utils import send_sms
from datetime import datetime
   




class ProcessPayment:
    def safaricom_stk_push_request(self, context):
        try:
            url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
            BASE_URL= frappe.get_single("Gym URL").url

            payload = {
                "BusinessShortCode": "4237271",
                "Password": f"{ self.get_env_data()['PASSWORD'] }",
                "Timestamp": "20240514183146",
                "TransactionType": "CustomerPayBillOnline",
                "Amount": f"{context['amount']}",
                "PartyA": f"{context['mobile_number']}",
                "PartyB": f"{context['paybill']}",
                "PhoneNumber": f"{context['mobile_number']}",
                "CallBackURL":  f"{BASE_URL}/api/method/gms.services.payments.stk_push_response",
                "AccountReference": f"{context['bank_account_number']}",
                "TransactionDesc": "Gym Payment"
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer { self.generate_access_token() }"
            }
            response = requests.request("POST", url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"{e}")
            return {'error': str(e)}, 400


    def generate_access_token(self):
        try:
            url = "https://api.safaricom.co.ke/oauth/v1/generate"

            querystring = {"grant_type":"client_credentials"}

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "insomnia/2023.5.8",
                "Authorization": f"Basic { self.get_env_data()['BEARER_TOKEN'] }"
            }

            response = requests.request("GET", url, headers=headers, params=querystring)

            resp = response.json()

            access_token = resp['access_token']

            return access_token
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"{e}")
            return {'error': str(e)}, 400



    def get_env_data(self):
        try:
            load_dotenv()
            BEARER_TOKEN = os.getenv('BEARER_TOKEN')
            PASSWORD = os.getenv('PASSWORD')

            context = {
                "BEARER_TOKEN": BEARER_TOKEN,
                "PASSWORD": PASSWORD
            }

            return context
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"{e}")
            return {'error': str(e)}, 400

payment = ProcessPayment()


@frappe.whitelist( allow_guest=True)
def make_payment(amount, mobile_number, invoice_number):
    try:
        existing_transaction_name = frappe.db.get_all(
            'Payment Transaction',
            filters={
                'invoice_number': invoice_number,
                'mobile_number': mobile_number,
                'status': 'Pending'
            },
            fields=['name']
        )
        
        if existing_transaction_name:
            for transaction in existing_transaction_name:
                frappe.db.delete("Payment Transaction", {
                    "name": transaction.name,
                })
        
        frappe.db.commit()
        payment_account = frappe.get_single("GMS Payment Account")
        paybill = payment_account.paybill
        account_number = payment_account.account_number
    

        doc = frappe.get_doc({
            'doctype': 'Payment Transaction',
            'invoice_number': invoice_number,
            'mobile_number': mobile_number,
            'amount': amount,
            'status': 'Pending',
             'date': datetime.now()
        })

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        context = {
            "paybill": paybill,
            "bank_account_number": account_number,
            "amount": amount,
            "mobile_number": format_mobile_number(mobile_number)
        }

        return payment.safaricom_stk_push_request(context)
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"{e}")
        return {'error': str(e)}, 400


@frappe.whitelist(allow_guest=True)
def stk_push_response():
    data = frappe.request.get_json(force=True)
    
    response = data['Body']['stkCallback'] 

    items = response['CallbackMetadata']['Item']


    Amount = next((item["Value"] for item in items if item["Name"] == "Amount"), None)
    MpesaReceiptNumber = next((item["Value"] for item in items if item["Name"] == "MpesaReceiptNumber"), None)
    TransactionDate = next((item["Value"] for item in items if item["Name"] == "TransactionDate"), None)
    PhoneNumber = next((item["Value"] for item in items if item["Name"] == "PhoneNumber"), None)

    reference_code = response['ResultCode']
    
    try:
        docs=frappe.get_all("MPesa Payment Transaction",{"mpesa_receipt_number":MpesaReceiptNumber},{"name"})
        if docs:
            for item in docs:
                frappe.db.delete("MPesa Payment Transaction", {
                    "name": item.name,
                })
            frappe.db.commit()
        doc = frappe.get_doc({
            'doctype': 'MPesa Payment Transaction',
            'merchant_request_id': response['MerchantRequestID'],
            'result_code': reference_code, 
            'amount': Amount,
            'mpesa_receipt_number': MpesaReceiptNumber,
            'transaction_date': TransactionDate,
            'mobile_number': PhoneNumber
        })

        doc.insert(ignore_permissions=True)
        frappe.db.commit()


        return process_payment_and_reconcile_member_invoice(MpesaReceiptNumber, TransactionDate, PhoneNumber, Amount)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"{e}")
        return {'error': str(e)}, 400 



@frappe.whitelist(allow_guest=True)
def process_payment_and_reconcile_member_invoice(MpesaReceiptNumber, TransactionDate, PhoneNumber, Amount):
    try:
        if not isinstance(PhoneNumber, str):
            PhoneNumber = str(PhoneNumber)

        standardized_phone_number = format_mobile_number_on_processing(PhoneNumber)  

        pending_transaction = frappe.get_all(
            'Payment Transaction', 
            filters={'mobile_number': standardized_phone_number, 'status': 'Pending'}, 
            fields=['name', 'invoice_number']
        )
                
        if not pending_transaction:
            return "no pending transaction"

        all=frappe.get_all("Mode of Payment Account",{"parent":"M-Pesa"},"default_account")
        if all:
            paid_to_account = all[0].default_account

        payment_reference = [{
            "reference_doctype": "Sales Invoice",
            "reference_name": pending_transaction[0].invoice_number,
            "allocated_amount": Amount
        }]

        customer = frappe.db.get_value("Sales Invoice", {"name": pending_transaction[0].invoice_number}, "customer")

        if not customer:
            frappe.log_error(f"No customer found for member with phone number {standardized_phone_number}", "Payment Reconciliation Error")
            return {'error': 'Customer not found'}, 404

        
        create_payment_entry("M-Pesa", customer, Amount, paid_to_account, MpesaReceiptNumber, TransactionDate, payment_reference, pending_transaction[0].name)
        
        def update_invoice_status(invoice_name):
            invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)
            invoice_doc.reload()
            new_status = "Paid" if invoice_doc.outstanding_amount == 0 else "Partly Paid"
            frappe.db.set_value("Sales Invoice", invoice_name, "status", new_status)

        update_invoice_status(pending_transaction[0].invoice_number)
        
        invoice_doc = frappe.get_doc("Sales Invoice", pending_transaction[0].invoice_number)

        frappe.db.commit()

        message = f" Dear {customer}, Thank you for your gms payment of {Amount}. It has been successfully received."
        send_sms(standardized_phone_number, message)

        return {
            'success': True,
            'message': 'Payment reconciled  with locker booking successfully',
            'invoice_number': pending_transaction[0].invoice_number
        }
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"{e}")
        return {'error': str(e)}, 400







@frappe.whitelist(allow_guest=True)
def format_mobile_number_on_processing(mobile_number):
    if isinstance(mobile_number, int):
        mobile_number = str(mobile_number) 

    if mobile_number.startswith("254"):
        return "0" + mobile_number[3:]  
    else:
        return mobile_number  
 

@frappe.whitelist(allow_guest=True)
def request_payment(invoice_number):
    pass










