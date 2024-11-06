import frappe
from frappe.model.document import Document
from gms.services.utils import send_sms
import random
from datetime import datetime, date
from gms.services.login import login
from frappe.utils import add_days

@frappe.whitelist()
def create_sales_invoice(doc, method):
    try:
        if doc.workflow_state == "Released" and not doc.sales_invoice_created:
            doc=frappe.get_doc("Gym Locker Booking", doc.name)
            if doc.booking_type == "Hours" and doc.start_time:
                now = datetime.now()
                doc.end_time = now
                if isinstance(doc.start_time, str):
                    doc.start_time = datetime.strptime(doc.start_time, "%Y-%m-%d %H:%M:%S")
                hours = (now - doc.start_time).total_seconds() // 3600 or 1
                doc.number_of_hours = int(hours) or 1
                rate = get_gym_settings().locker_price_per_hour
                qty = hours

            elif doc.booking_type == "Days" and doc.start_date:
                today = date.today()
                doc.end_date = today
                days = (today - doc.start_date).days 
                doc.number_of_days = days or 1
                rate = get_gym_settings().locker_price_per_day
                qty = days  or 1
            doc.sales_invoice_created = 1
            doc.save()

            exists = frappe.db.get_all("Sales Invoice", {"custom_locker_booking": doc.name},{"name"})
            if not exists and rate and qty:
                items = [{
                    "item_code": "Locker",
                    "item_name":"Locker",
                    "rate": rate,
                    "qty": qty
                }]
                member = frappe.get_doc("Gym Member", doc.member)
                due_days = get_gym_settings().sales_invoice_due_days
                due_date = add_days(frappe.utils.nowdate(), due_days)
                
                invoice = frappe.get_doc({
                    "doctype": "Sales Invoice",
                    "customer": member.full_name,
                    "custom_locker_booking": doc.name,
                    "due_date": due_date,
                    "items": items
                })
                invoice.insert(ignore_permissions=True)
                invoice.save()

            locker=frappe.get_doc("Gym Locker Number", doc.locker_number)
            locker.status="Vacant"
            locker.occupant=""
            locker.save()
            frappe.db.commit()
            return "success"
        elif doc.workflow_state == "Reserved":
            locker=frappe.get_doc("Gym Locker Number", doc.locker_number)
            locker.status="Occupied"
            locker.occupant=doc.member
            locker.save()
            frappe.db.commit()
            return

    except Exception as e:
        frappe.log_error(message=str(e), title="Sales Invoice Creation Error")
        frappe.throw("An error occurred while creating the Sales Invoice.")


@frappe.whitelist()
def get_gym_settings():
    gym_settings = frappe.get_single("Gym Settings")
    return gym_settings

@frappe.whitelist()
def before_inserting_gym_member(doc, method):
    if doc.mobile_number and len(doc.mobile_number) > 10:
        frappe.throw("Phone number should not be more than 10 digits.")

    if doc.id_number and len(doc.id_number) > 9:
        frappe.throw("ID number should not be more than 9 digits.")

    if not doc.email:
        gym_name = get_gym_settings().gym_name.replace(" ", "").lower()
        doc.email = f"{doc.mobile_number}@{gym_name}.com"

        if frappe.db.exists("User", doc.email):
            frappe.throw(f"A user with the email {doc.email} already exists. Please use a unique email.")

    doc.member_id = generate_unique_member_no()

@frappe.whitelist()
def after_inserting_gym_member(doc, method):
  try:
    frappe.enqueue(
    create_customer_and_user_for_member,
                queue="default",
                timeout=300,
                is_async=True,
                now=False,
                full_name=doc.full_name,
                member_id=doc.member_id,
                email=doc.email,
                mobile_number=doc.mobile_number
            )
  except Exception as e:
    frappe.log_error(frappe.get_traceback(), f"{e}")
    frappe.throw(f"Member could not be created: {str(e)}")

@frappe.whitelist()
def generate_unique_member_no():
    current_year = str(frappe.utils.now_datetime().year)[-2:]
    current_month = str(frappe.utils.now_datetime().month)

    if current_month.startswith('0'):
        current_month = current_month[1]

    while True:
        random_digits = str(random.randint(1000, 9999))
        member_id = f"MEM{current_year}{current_month}{random_digits}"

        if not frappe.db.exists("Gym Member", {"member_id": member_id}):
            return member_id

@frappe.whitelist()
def create_customer_and_user_for_member(full_name, member_id, email, mobile_number):
    try:
        create_customer(full_name, member_id)
        password = str(create_user_for_member(full_name, email, mobile_number))

        login_url = frappe.utils.get_url()
        message = (
            f"Hello {full_name}, Welcome to {get_gym_settings().gym_name}. "
            f"Your login details are as follows:\n"
            f"User Name: {mobile_number}\n"
            f"Password: {password}\n"
            f"Login URL: {login_url}\n"
            f"Please log in and change your password as soon as possible."
        )
        print("Message prepared for sending SMS.")

        # Send SMS
        frappe.enqueue(
            send_sms,
            queue="default",
            timeout=300,
            is_async=True,
            now=False,
            mobile=mobile_number,
            message=message
        )
        print(f"Password sent successfully to {mobile_number}")

    except Exception as e:
        # Log error with traceback
        frappe.log_error(frappe.get_traceback(), f"Error in customer or user creation: {e}")
        print(f"An error occurred: {e}") 

@frappe.whitelist()
def create_customer(full_name, member_id):
    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": full_name,
        "customer_group": "Individual",
        "customer_type": "Individual",
        "custom_gym_member": member_id,
        "territory": "Kenya"
    })
    customer.insert(ignore_mandatory=True)
    frappe.db.commit()
    return True

@frappe.whitelist()
def create_user_for_member(full_name, email, mobile_number):
    password = str(generate_simple_password())
    user = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": full_name,
        "enabled": 1,
        "new_password": password,
        "mobile_no": mobile_number,
        "send_welcome_email": 1,
        "user_type": "System User",
        "module_profile": "Member",
        "roles": [
            {"role": "Member"}
        ],
        "ignore_password_policy": 1  
    })
    user.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.msgprint(f"User {full_name} has been created successfully.")
    return password  

def generate_simple_password():
    return (random.randint(1000, 9999))


@frappe.whitelist()
def before_inserting_gym_trainer(doc, method):
    if doc.mobile_number and len(doc.mobile_number) > 10:
        frappe.throw("Phone number should not be more than 10 digits.")
    
    if doc.id_number and len(doc.id_number) > 9:
        frappe.throw("ID number should not be more than 9 digits.")
    
    if not doc.email:
        gym_name = get_gym_settings().gym_name.replace(" ", "").lower()
        doc.email = f"{doc.mobile_number}@{gym_name}.com"
        
        if frappe.db.exists("User", doc.email):
            frappe.throw(f"A user with the email {doc.email} already exists. Please use a unique email.")
    
    doc.trainer_id = generate_unique_trainer_no()

@frappe.whitelist()
def after_inserting_gym_trainer(doc, method):
    try:
        frappe.enqueue(
            create_employee_and_user_for_trainer,
            queue="default",
            timeout=300,
            is_async=True,
            now=False,
            doc=doc,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"{e}")
        frappe.throw(f"Member could not be created: {str(e)}")

@frappe.whitelist()
def generate_unique_trainer_no():
    current_year = str(frappe.utils.now_datetime().year)[-2:]
    current_month = str(frappe.utils.now_datetime().month).lstrip('0')
    
    while True:
        random_digits = str(random.randint(1000, 9999))
        trainer_id = f"TR{current_year}{current_month}{random_digits}"
        
        if not frappe.db.exists("Gym Trainer", {"trainer_id": trainer_id}):
            return trainer_id

@frappe.whitelist()
def create_employee_and_user_for_trainer(doc):
    try:
        create_employee(doc)
        password = create_user_for_trainer(doc)
        
        login_url = frappe.utils.get_url()
        message = (
            f"Hello {doc.full_name}, Welcome to {get_gym_settings().gym_name}. "
            f"Your login details are as follows:\n"
            f"User Name: {doc.mobile_number}\n"
            f"Password: {password}\n"
            f"Login URL: {login_url}\n"
            f"Please log in and change your password as soon as possible."
        )
        
        frappe.enqueue(
            send_sms,
            queue="default",
            timeout=300,
            is_async=True,
            now=False,
            mobile=doc.mobile_number,
            message=message
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Error in customer or user creation: {e}")
        frappe.throw(f"An error occurred: {e}")

@frappe.whitelist()
def create_employee(doc):
    employee = frappe.get_doc({
        "doctype": "Employee",
        "first_name": doc.full_name,
        "gender": doc.gender,
        "date_of_joining": doc.date_of_joining,
        "employee_number": doc.trainer_id,
    })
    employee.insert(ignore_mandatory=True)
    frappe.db.commit()
    return True

@frappe.whitelist()
def create_user_for_trainer(doc):
    password = str(generate_simple_password())
    user = frappe.get_doc({
        "doctype": "User",
        "email": doc.email,
        "first_name": doc.full_name,
        "enabled": 1,
        "new_password": password,
        "mobile_no": doc.mobile_number,
        "send_welcome_email": 1,
        "user_type": "System User",
        "module_profile": "Trainer",
        "roles": [{"role": "Trainer"}],
        "ignore_password_policy": 1  
    })
    user.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.msgprint(f"User {doc.full_name} has been created successfully.")
    return password



@frappe.whitelist(allow_guest=True)
def add_locker_numbers():
    for locker_number in range(1, 101):
        customer = frappe.get_doc({
            "doctype": "Gym Locker Number",
            "locker_number": locker_number,
        })
        customer.insert(ignore_permissions=True)
    frappe.db.commit()
    return True

@frappe.whitelist(allow_guest=True)
def return_locker_booking():
    return frappe.get_all("Gym Locker Booking",{},{"*"})



