import frappe
import requests
import os
from dotenv import load_dotenv
from gms.services.utils import format_mobile_number
from gms.services.utils import create_payment_entry
from gms.services.utils import send_sms
from datetime import datetime
from gms.services.rest import update_mgr_status, enqueue_member_contribution, update_table_banking_fund, process_loan_repayment




class ProcessPayment:
    def safaricom_stk_push_request(self, payload):
        try:
            url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

            payload = {
                "BusinessShortCode": "4237271",
                "Password": f"{ self.get_env_data()['PASSWORD'] }",
                "Timestamp": "20240514183146",
                "TransactionType": "CustomerPayBillOnline",
                "Amount": f"{payload['amount']}",
                "PartyA": f"{payload['mobile_number']}",
                "PartyB": f"{payload['paybill']}",
                "PhoneNumber": f"{payload['mobile_number']}",
                "CallBackURL": "https://7895-102-212-236-161.ngrok-free.app/api/method/gms.services.payments.stk_push_response",
                "AccountReference": f"{payload['bank_account_number']}",
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


@frappe.whitelist(methods=['GET'], allow_guest=True)
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
        

        for transaction in existing_transaction_name:
            frappe.db.delete("Payment Transaction", {
                "name": transaction.name,
            })
        
        frappe.db.commit()
        paybill, account_number = frappe.db.get_value('GMS Payment Account', None, ['paybill', 'account_number'])

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
    # data = frappe.request.get_json(force=True)

    data={'Body': {'stkCallback': {'MerchantRequestID': '4f9d-4622-a0da-1c77977dad0c137103410', 
    'CheckoutRequestID': 'ws_CO_11112024114458752768135284', 'ResultCode': 0,
     'ResultDesc': 'The service request is processed successfully.',
     'CallbackMetadata': {'Item': [{'Name': 'Amount', 'Value': 1.0}, {'Name': 'MpesaReceiptNumber', 'Value': 'SKB5EAPG87'}, {'Name': 'Balance'}, {'Name': 'TransactionDate', 'Value': 20241111114510}, {'Name': 'PhoneNumber', 'Value': 254768135284}]}}}}


    response = data['Body']['stkCallback'] 

    items = response['CallbackMetadata']['Item']
    

    Amount = next((item["Value"] for item in items if item["Name"] == "Amount"), None)
    MpesaReceiptNumber = next((item["Value"] for item in items if item["Name"] == "MpesaReceiptNumber"), None)
    TransactionDate = next((item["Value"] for item in items if item["Name"] == "TransactionDate"), None)
    PhoneNumber = next((item["Value"] for item in items if item["Name"] == "PhoneNumber"), None)

    reference_code = response['ResultCode']
    
    
    try:
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




def process_payment_and_reconcile_member_invoice(MpesaReceiptNumber, TransactionDate, PhoneNumber, Amount):
    try:
        data={'Body': {'stkCallback': {'MerchantRequestID': '4f9d-4622-a0da-1c77977dad0c137103410', 
        'CheckoutRequestID': 'ws_CO_11112024114458752768135284', 'ResultCode': 0,
        'ResultDesc': 'The service request is processed successfully.',
        'CallbackMetadata': {'Item': [{'Name': 'Amount', 'Value': 1.0}, {'Name': 'MpesaReceiptNumber', 'Value': 'SKB5EAPG87'}, {'Name': 'Balance'}, {'Name': 'TransactionDate', 'Value': 20241111114510}, {'Name': 'PhoneNumber', 'Value': 254768135284}]}}}}


        response = data['Body']['stkCallback'] 

        items = response['CallbackMetadata']['Item']
        

        Amount = next((item["Value"] for item in items if item["Name"] == "Amount"), None)
        MpesaReceiptNumber = next((item["Value"] for item in items if item["Name"] == "MpesaReceiptNumber"), None)
        TransactionDate = next((item["Value"] for item in items if item["Name"] == "TransactionDate"), None)
        PhoneNumber = next((item["Value"] for item in items if item["Name"] == "PhoneNumber"), None)

        if not isinstance(PhoneNumber, str):
            PhoneNumber = str(PhoneNumber)

        standardized_phone_number = format_mobile_number_on_processing(PhoneNumber)  

        pending_transaction = frappe.get_all(
            'Payment Transaction', 
            filters={'mobile_number': standardized_phone_number, 'status': 'Pending'}, 
            fields=['name', 'invoice_number']
        )
                
        if not pending_transaction:
            return

        paid_to_account = frappe.db.get_value("Mode of Payment Account", {"parent": "M-Pesa"}, "default_account")

        payment_reference = [{
            "reference_doctype": "Sales Invoice",
            "reference_name": pending_transaction[0].invoice_number,
            "allocated_amount": Amount
        }]

        customer = frappe.db.get_value("Sales Invoice", {"name": pending_transaction[0].invoice_number}, "customer")
        return customer

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

        if invoice_doc.custom_contribution_type:
            member_name = frappe.db.get_value("Customer", {"name": customer}, "custom_chamaa_member")

            if member_name:
                current_month = datetime.now().strftime("%B")
                month_to_use = invoice_doc.custom_invoice_month if invoice_doc.custom_invoice_month else current_month
                
                enqueue_member_contribution(
                    member=member_name,
                    amount=Amount,
                    contribution_type=invoice_doc.custom_contribution_type,
                    month=month_to_use,  
                    date_of_contribution=TransactionDate,
                    phone_number=standardized_phone_number,
                    invoice_name=pending_transaction[0].invoice_number, 
                    merry_go_round_number=invoice_doc.custom_merry_go_round_number,  
                    table_banking_fund_number=invoice_doc.custom_table_banking_number 
                )

        if invoice_doc.custom_contribution_type == "Merry Go Round":
            round_number = invoice_doc.custom_merry_go_round_number  
            update_mgr_status(round_number, pending_transaction[0].invoice_number, Amount) 

        elif invoice_doc.custom_contribution_type == "Table Banking Fund":
            table_banking_fund_number = invoice_doc.custom_table_banking_number
            update_table_banking_fund(
                member=member_name,
                amount=Amount,
                date_of_contribution=TransactionDate,
                table_banking_fund_number=table_banking_fund_number
            )
        elif invoice_doc.custom_contribution_type == "Loan Repayment":
            loan_name = frappe.db.get_value('Loan', {'loan_invoice': invoice_doc.name}, 'name')
            if loan_name:
                process_loan_repayment(
                    loan_name=loan_name,
                    amount_to_pay=Amount,
                    invoice_name=invoice_doc.name
                )

        frappe.db.commit()

        full_name = frappe.db.get_value('Member', {"name": member_name}, "full_name")
        message = f" Dear {full_name}, Thank you for your {invoice_doc.custom_contribution_type} contribution of {Amount}. It has been successfully received."
        send_sms(standardized_phone_number, message)

        return {
            'success': True,
            'message': 'Payment reconciled and Member Contribution created successfully',
            'invoice_number': pending_transaction[0].invoice_number
        }
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"{e}")
        return {'error': str(e)}, 400







def format_mobile_number_on_processing(mobile_number):
    if isinstance(mobile_number, int):
        mobile_number = str(mobile_number) 

    if mobile_number.startswith("254"):
        return "0" + mobile_number[3:]  
    else:
        return mobile_number  
 

def request_payment(invoice_number):
    pass










