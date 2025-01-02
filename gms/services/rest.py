import frappe
from frappe.model.document import Document
from gms.services.utils import send_sms
import random
from datetime import datetime, date
from gms.services.login import login
from frappe.utils import add_months, add_days
from gms.services.payments import make_payment
from gms.services.whatsapp import send_invoice_whatsapp
    

@frappe.whitelist(allow_guest=True)
def calculate_total_rating(instructor):
    try:
        ratings = frappe.get_all("Rating", {"instructor": instructor}, {"rating"})
        tot_ratings = len(ratings)
        sum_ratings = 0
        for rating in ratings:
            sum_ratings += rating.rating
        if sum_ratings:
            average_rating = sum_ratings / tot_ratings
            frappe.db.sql(
                """
                UPDATE `tabGym Trainer`
                SET total_ratings = %s,
                average_ratings = %s
                WHERE name = %s
                """,
                (tot_ratings, average_rating, instructor)
            )
            frappe.db.commit()
            return True
    except Exception as e:
        frappe.log_error(f"Error in calculate_total_rating: {str(e)}")
        return False

@frappe.whitelist(allow_guest=True)
def get_group_class_members(group_class):
    try:
        classes = frappe.get_all(
            "Join Class",
            filters={"group_class": group_class, "docstatus": 1},
            fields=["gym_member"]
        )
        members = [item["gym_member"] for item in classes if item.get("gym_member")]
        return members if members else []
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_group_class_members")



@frappe.whitelist(allow_guest=True)
def get_total_attendance(name):
    try:
        present_members = frappe.get_all(
            "Class Attendance",
            filters={"parent": name, "presence": "Present"},
            fields=["name"]
        )
        total_attendance = len(present_members)

        frappe.db.sql(
            """
            UPDATE `tabAttendance`
            SET total_attendance = %s
            WHERE name = %s
            """,
            (total_attendance, name)
        )
        frappe.db.commit()
        return True

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_total_attendance")
        return False


@frappe.whitelist()
def get_permission_query_conditions_for_trainer(user, doctype):
    try:
        if user != "Administrator": 
            user_doc = frappe.get_doc("User", user)
            user_roles = [role.role for role in user_doc.roles]

            if user_roles == ["Trainer"]:
                trainer_doc = frappe.get_doc("Gym Trainer", {"email": user})
                
                if doctype == "Gym Trainer":
                    return f"(`tab{doctype}`.email = '{trainer_doc.email}')"
                elif doctype == "Group Class":
                    return f"(`tab{doctype}`.instructor = '{trainer_doc.name}')"
            else:
                return
        else:
            return 

    except frappe.DoesNotExistError as e:
        frappe.log_error(f"Document not found: {e}", "Permission Query Error")
        return ""

    except Exception as e:
        frappe.log_error(f"An error occurred: {e}", "Permission Query Error")
        return ""




@frappe.whitelist(allow_guest=True)
def enroll_fingerprint_id(fingerprint_id):
    try:
      
        frappe.get_doc({
                "doctype": "User Access",
                "fingerprint_id":fingerprint_id,
                "date": frappe.utils.nowdate()
            }).insert(ignore_permissions=True)
        return True
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in check_user_access")
        return False

@frappe.whitelist(allow_guest=True)
def check_user_access(fingerprint_id):
    try:
        print(f"\n\n\n{fingerprint_id}\n\n\n")
        user_access = frappe.get_all(
            "User Access",
            filters={"fingerprint": fingerprint_id},
            fields=["user_id"]
        )

        if user_access:
            frappe.get_doc({
                "doctype": "Attendance List",
                "member": user_access[0].get("user_id"),
                "date": frappe.utils.nowdate(),
                "time": frappe.utils.nowtime()
            }).insert(ignore_permissions=True)
            return True

        return False
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in check_user_access")
        return False


@frappe.whitelist(allow_guest=True)
def get_current_month(doc):
    month = datetime.now().strftime("%B")
    gym_settings = frappe.get_single("Gym Settings")
    gym_name = gym_settings.gym_name
    return f"{gym_name}, {month}"  


@frappe.whitelist(allow_guest=True)
def get_invoice_pay_link(doc):
    BASE_URL = frappe.utils.get_url()
    customer=frappe.get_value("Customer",{"name":doc.customer}, "custom_gym_member")
    phone=frappe.get_value("Gym Member",{"name":customer}, "mobile_number")
    URL =f"{BASE_URL}/payment-requests/new?amount={doc.outstanding_amount}&mobile_number={phone}&sales_invoice={doc.name}"
    return URL


@frappe.whitelist(allow_guest=True)
def call_make_payment(doc, method):
    make_payment(round(doc.amount), doc.mobile_number, doc.sales_invoice)
    return True

@frappe.whitelist(allow_guest=True)
def fetch_class_attendees(group_class):
    members = frappe.get_all(
        "Join Class",
        filters={"docstatus": 1, "group_class": group_class},
        fields=["gym_member","phone","member_name"],
        distinct=True
    )
    
    unique_members = [{"member_id":member.gym_member,"member": member.member_name,"mobile_number":member.phone} for member in members]
    return unique_members

@frappe.whitelist(allow_guest=True)
def after_inserting_gym_machine(doc, method):
    try:
        doc=frappe.get_doc("Gym Cardio Machine", doc)
        base_id = doc.machine_name.strip().replace(" ", "_").lower()
        machine_id = base_id
        counter = 1

        while frappe.db.exists("Gym Cardio Machine", machine_id):
            machine_id = f"{base_id}_{counter}"
            counter += 1

        doc.machine_name = machine_id
        # doc.name = machine_id
        doc.save()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"{e}")
        frappe.throw(f"Machine could not be created: {str(e)}")

@frappe.whitelist(allow_guest=True)
def get_cardio_machine():
    login("administrator",".")
    machines=frappe.get_all("Gym Cardio Machine",{},{"name"})
    for machine in machines:
        doc=frappe.get_doc("Gym Cardio Machine",machine.name)
        doc.current_status="Available"
        doc.save()
    frappe.db.commit()
    return "successfull"






@frappe.whitelist(allow_guest=True)
def get_permission_query_conditions(user, doctype):
    try:
        if user != "Administrator":
            user_roles = frappe.get_doc("User", user)
            if ['Member']== [role.role for role in user_roles.roles]:
                doc = frappe.get_doc("Gym Member", {"email": user})
                if doctype == "Gym Member":
                    return f"(`tab{doctype}`.email = '{user}')"
                elif doctype in ["Gym Locker Booking", "Gym Membership"]:
                    return f"(`tab{doctype}`.member = '{doc.name}')"
                elif doctype == "Join Class":
                    return f"(`tab{doctype}`.gym_member = '{doc.name}')"
                elif doctype == "Rating":
                    return f"(`tab{doctype}`.member = '{doc.name}')"
            else:
                return  
        else:
            return 
    except frappe.DoesNotExistError as e:
        frappe.log_error(f"Document not found: {e}", "Permission Query Error")
        return ""
    except Exception as e:
        frappe.log_error(f"An error occurred: {e}", "Permission Query Error")
        return ""


@frappe.whitelist(allow_guest=True)
def create_sales_invoice_for_group_class(doc, method):
    try:
        doc = frappe.get_doc("Join Class", doc.name)
        if doc.docstatus == 1:
            items = [{
                "item_code": "Group Class",
                "custom_join_class_id": doc.name,
                "rate": doc.price,
                "qty": 1
            }]
            member = frappe.get_doc("Gym Member", doc.gym_member)
            due_days = get_gym_settings().sales_invoice_due_days
            due_date = add_days(frappe.utils.nowdate(), due_days)

            invoice = frappe.get_doc({
                "doctype": "Sales Invoice",
                "customer": member.full_name,
                "due_date": due_date,
                "custom_payment_type": "Group Class",
                "items": items,
            })
            invoice.insert(ignore_permissions=True)
            invoice.submit()
            invoice.save()

            frappe.db.commit()

        return True
    except Exception as e:
        frappe.log_error(f"Error creating sales invoice: {e}")
        return {"error": str(e)}

@frappe.whitelist(allow_guest=True)
def create_sales_invoice_for_membership(doc,method):
    try:
        doc = frappe.get_doc("Gym Membership", doc.name)
        if doc.docstatus == 1:
            exists = frappe.get_all("Sales Invoice Item", {"custom_gym_membership": doc.name}, {"name"})
            if not exists:
                if doc.membership_type == "Standard":
                    rate = get_gym_settings().standard_membership_price
                elif doc.membership_type == "Premium":
                    rate = get_gym_settings().premium_membership_price
                elif doc.membership_type == "VIP":
                    rate = get_gym_settings().vip_membership_price
                else:
                    rate = 0

                if doc.plan_type == "Monthly":
                    qty = 1
                    end_date = add_months(doc.date_of_subscription, 1)
                elif doc.plan_type == "Quarterly":
                    qty = 3
                    end_date = add_months(doc.date_of_subscription, 3)
                elif doc.plan_type == "Annually":
                    qty = 12
                    end_date = add_months(doc.date_of_subscription, 12)
                else:
                    qty = 0

                items = [{
                    "item_code": "Membership",
                    "item_name": "Membership",
                    "custom_gym_membership": doc.name,
                    "rate": rate,
                    "qty": qty
                }]
                member = frappe.get_doc("Gym Member", doc.member)
                member.sub_end_date=end_date
                member.sub_start_date=doc.date_of_subscription
                member.membership_type=doc.membership_type
                member.plan_type=doc.plan_type
                member.save()
                due_days = get_gym_settings().sales_invoice_due_days
                due_date = add_days(frappe.utils.nowdate(), due_days)

                invoice = frappe.get_doc({
                    "doctype": "Sales Invoice",
                    "customer": member.full_name,
                    "due_date": due_date,
                    "custom_payment_type":"Membership Subscription",
                    "items": items,
                })
                invoice.insert(ignore_permissions=True)
                invoice.submit()
                invoice.save()
    
                frappe.db.commit()
                
                gym_member = frappe.get_doc("Gym Member",doc.member)

                send_invoice_whatsapp(gym_member.mobile_number, invoice.name)

        return True
    except Exception as e:
        frappe.log_error(f"Error creating sales invoice: {e}")
        return {"error": str(e)}


@frappe.whitelist(allow_guest=True)
def create_sales_invoice_for_locker_booking(doc, method):
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
                member.locker_booked=None
                member.save()
                due_days = get_gym_settings().sales_invoice_due_days
                due_date = add_days(frappe.utils.nowdate(), due_days)
                
                invoice = frappe.get_doc({
                    "doctype": "Sales Invoice",
                    "customer": member.full_name,
                    "custom_locker_booking": doc.name,
                    "custom_payment_type":"Locker Charges",
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
            member = frappe.get_doc("Gym Member", doc.member)
            member.locker_booked=doc.locker_number
            member.save()
            frappe.db.commit()
            return

    except Exception as e:
        frappe.log_error(message=str(e), title="Sales Invoice Creation Error")
        frappe.throw("An error occurred while creating the Sales Invoice.")


@frappe.whitelist(allow_guest=True)
def get_gym_settings():
    gym_settings = frappe.get_single("Gym Settings")
    return gym_settings


@frappe.whitelist(allow_guest=True)
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

    doc.member_no = generate_unique_member_no()


@frappe.whitelist(allow_guest=True)
def after_inserting_gym_member(doc, method):
  try:
    # doc=frappe.get_doc("Gym Member",doc)
    frappe.enqueue(
    create_customer_and_user_for_member,
                queue="default",
                timeout=300,
                is_async=True,
                now=False,
                full_name=doc.full_name,
                member_id=doc.member_no,
                email=doc.email,
                mobile_number=doc.mobile_number
            )
  except Exception as e:
    frappe.log_error(frappe.get_traceback(), f"{e}")
    frappe.throw(f"Member could not be created: {str(e)}")


@frappe.whitelist(allow_guest=True)
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


@frappe.whitelist(allow_guest=True)
def create_customer_and_user_for_member(full_name, member_id, email, mobile_number):
    try:
        create_customer(full_name, member_id, email)

        password = str(create_user_for_member(full_name, email, mobile_number))

        # login_url = frappe.utils.get_url()
        login_url = frappe.get_single("Gym URL").url
        message = (
            f"Hello {full_name}, Welcome to {get_gym_settings().gym_name}. "
            f"Your login details are as follows:\n"
            f"User Name: {mobile_number}\n"
            f"Password: {password}\n"
            f"Login URL: {login_url}\n"
            f"Please log in and change your password as soon as possible."
        )
        print("Message prepared for sending SMS.")
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


@frappe.whitelist(allow_guest=True)
def get_single():
    return frappe.get_single("Gym URL").url

@frappe.whitelist(allow_guest=True)
def create_customer(full_name, member_id, email):

    customer = frappe.get_doc({
        "doctype":"Customer",
        "customer_name": full_name,
        "customer_group": "Individual",
        "customer_type": "Individual",
        "custom_gym_member": email,
        "territory": "Kenya"
    })
    customer.insert(ignore_mandatory=True)
    frappe.db.commit()
    return True

@frappe.whitelist(allow_guest=True)
def create_user_for_member(full_name, email, mobile_number):
    password = str(generate_simple_password())
    user = frappe.get_doc({
        "doctype":"User",
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

@frappe.whitelist(allow_guest=True)
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

@frappe.whitelist(allow_guest=True)
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

@frappe.whitelist(allow_guest=True)
def generate_unique_trainer_no():
    current_year = str(frappe.utils.now_datetime().year)[-2:]
    current_month = str(frappe.utils.now_datetime().month).lstrip('0')
    
    while True:
        random_digits = str(random.randint(1000, 9999))
        trainer_id = f"TR{current_year}{current_month}{random_digits}"
        
        if not frappe.db.exists("Gym Trainer", {"trainer_id": trainer_id}):
            return trainer_id


@frappe.whitelist(allow_guest=True)
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


@frappe.whitelist(allow_guest=True)
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


@frappe.whitelist(allow_guest=True)
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



