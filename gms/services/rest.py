import frappe
from frappe.model.document import Document
from gms.services.utils import send_sms
import random

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

    doc.member_no = generate_unique_member_no(doc)

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
                member_id=doc.name,
                email=doc.email,
                mobile_number=doc.mobile_number
            )
  except Exception as e:
    frappe.log_error(frappe.get_traceback(), f"{e}")
    frappe.throw(f"Member could not be created: {str(e)}")

@frappe.whitelist()
def generate_unique_member_no(doc):
    current_year = str(frappe.utils.now_datetime().year)[-2:]
    current_month = str(frappe.utils.now_datetime().month)

    if current_month.startswith('0'):
        current_month = current_month[1]

    while True:
        random_digits = str(random.randint(1000, 9999))
        member_no = f"{current_year}{current_month}{random_digits}"

        if not frappe.db.exists("Gym Member", {"member_no": member_no}):
            return member_no

@frappe.whitelist()
def create_customer_and_user_for_member(full_name, member_id, email, mobile_number):
    try:
        create_customer(full_name, member_id)
        password = str(create_user_for_member(full_name, email, mobile_number))


        # Prepare the login message
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
    print(f"\n\n\n{full_name, email, mobile_number}")
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
