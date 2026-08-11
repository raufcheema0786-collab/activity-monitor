import sys
from urllib.parse import urlparse, parse_qs

import requests
from auth_storage import get_active_employee_id, save_token
from settings_storage import save_settings
from sync_service import get_settings

BACKEND_URL = "http://127.0.0.1:8000"


def get_incoming_link():
    for arg in sys.argv[1:]:
        if arg.startswith("employee-monitor://"):
            return arg
    return None


def parse_token_from_link(link):
    parsed = urlparse(link)
    query = parse_qs(parsed.query)
    token_list = query.get("token")
    if not token_list:
        return None
    return token_list[0]


def activate_with_backend(token):
    previous_employee_id = get_active_employee_id()

    response = requests.post(f"{BACKEND_URL}/employees/activate", json={"token": token})
    if response.status_code == 200:
        data = response.json()
        save_token(data["access_token"], data["employee_name"])
        new_employee_id = get_active_employee_id()
        if previous_employee_id is not None and previous_employee_id != new_employee_id:
            print(
                f"[activation] this machine previously belonged to employee_id={previous_employee_id}, "
                f"now activated for employee_id={new_employee_id} ('{data['employee_name']}'). "
                "Local monitor.db data from the previous employee is kept but excluded from this "
                "employee's totals via employee_id scoping."
            )
        fetched_settings = get_settings()
        if fetched_settings:
            save_settings(fetched_settings)
        return True, data["employee_name"]
    else:
        return False, response.json().get("detail", "Activation failed")


def handle_activation_if_present():
    link = get_incoming_link()
    if not link:
        return None

    token = parse_token_from_link(link)
    if not token:
        return None

    return activate_with_backend(token)
