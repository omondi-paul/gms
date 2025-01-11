app_name = "gms"
app_title = "Gms"
app_publisher = "Polito"
app_description = "An app for managing a fintness center"
app_email = "okemopaulo@gmail.comj"
app_license = "mit"

permission_query_conditions = {
            "Gym Locker Booking": "gms.services.rest.get_permission_query_conditions",
            "Sales Invoice": "gms.services.rest.get_permission_query_conditions",
            "Gym Membership": "gms.services.rest.get_permission_query_conditions",
            "Customer": "gms.services.rest.get_permission_query_conditions",
            "MPesa Payment Transaction": "gms.services.rest.get_permission_query_conditions",
            "Gym Member": "gms.services.rest.get_permission_query_conditions",
            "Rating": "gms.services.rest.get_permission_query_conditions",
            "Gym Trainer": "gms.services.rest.get_permission_query_conditions_for_trainer",
             "Group Class": "gms.services.rest.get_permission_query_conditions_for_trainer",
            "Join Class": "gms.services.rest.get_permission_query_conditions",
            }


doc_events = {
    "Gym Member": {
        "before_insert": "gms.services.rest.before_inserting_gym_member",
        "after_insert": "gms.services.rest.after_inserting_gym_member"
    },
   "Gym Trainer": {
        "before_insert": "gms.services.rest.before_inserting_gym_trainer",
        "after_insert": "gms.services.rest.after_inserting_gym_trainer"
    },
    "Gym Locker Booking": {
        "after_save": "gms.services.rest.fill_time",
         "on_update": "gms.services.rest.create_sales_invoice_for_locker_booking"
    },
     "Gym Membership": {
         "on_update": "gms.services.rest.create_sales_invoice_for_membership"
    },
     "Gym Cardio Machine": {
         "on_insert": "gms.services.rest.after_inserting_gym_machine"
    },
    "Request Payment": {
        "after_insert": "gms.services.rest.call_make_payment"
    },
     "Join Class": {
         "on_update": "gms.services.rest.create_sales_invoice_for_group_class"
    },
}


fixtures = [
  "Workspace",
  "Role",
  "Custom DocPerm",
  "Gym Locker Number",
  "Custom Field",
  "Role Profile",
  "Module Profile",
  "Workflow",
  "Workflow Action Master",
  "Workflow State",
  "Gym Cardio Machine",
  "Location",
  "Group Class",
  "Print Format",
  "Membership Type",
  "Payment Type",
  "Letter Head",
  "Workout Tag",
  "Gym Location",
  "Plan Type",
  "GMS Payment Account",
  "Gym Settings",
  "Gym URL", 
  "Item",
  "Whatsapp Settings",
  "Mode of Payment",
  "Client Script"


]

jinja = {
    "methods": [  
     "gms.services.rest.get_invoice_pay_link",
     "gms.services.rest.get_current_month"   
    ]
}

