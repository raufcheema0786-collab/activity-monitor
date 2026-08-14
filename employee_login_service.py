"""Network calls needed to get the local login gate working, deliberately
kept separate from sync_service.py: everything in sync_service assumes a
still-valid access token already exists, but the whole point of this login
gate is to work even when it doesn't (an expired token is exactly the case
that sends someone back to the login screen)."""
import requests

from auth_storage import get_active_employee_id, get_active_organization_id, save_token
from backend_config import BACKEND_URL


def get_login_state(timeout=5):
    """Returns one of:
    {"state": "not_activated"}
    {"state": "create_password", "employee_name": str}
    {"state": "login", "employee_name": str}
    {"state": "error", "error": str}
    """
    employee_id = get_active_employee_id()
    if employee_id is None:
        return {"state": "not_activated"}

    try:
        response = requests.get(f"{BACKEND_URL}/employees/{employee_id}/auth-state", timeout=timeout)
    except requests.exceptions.RequestException as e:
        return {"state": "error", "error": f"Can't reach the monitoring server: {e}"}

    if response.status_code != 200:
        return {"state": "error", "error": f"HTTP {response.status_code}: {response.text[:200]}"}

    data = response.json()
    return {
        "state": "create_password" if not data["has_password"] else "login",
        "employee_name": data["employee_name"],
    }


def set_password(password, timeout=5):
    employee_id = get_active_employee_id()
    if employee_id is None:
        return {"success": False, "error": "This machine hasn't been activated yet."}

    try:
        response = requests.post(
            f"{BACKEND_URL}/employees/set-password",
            json={"employee_id": employee_id, "password": password},
            timeout=timeout,
        )
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Can't reach the monitoring server: {e}"}

    if response.status_code != 200:
        return {"success": False, "error": response.json().get("detail", f"HTTP {response.status_code}")}

    return {"success": True}


def login(password, timeout=5):
    employee_id = get_active_employee_id()
    if employee_id is None:
        return {"success": False, "error": "This machine hasn't been activated yet."}

    try:
        response = requests.post(
            f"{BACKEND_URL}/employees/login",
            json={"employee_id": employee_id, "password": password},
            timeout=timeout,
        )
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Can't reach the monitoring server: {e}"}

    if response.status_code != 200:
        return {"success": False, "error": response.json().get("detail", f"HTTP {response.status_code}")}

    data = response.json()
    save_token(data["access_token"], data["employee_name"])
    return {"success": True, "employee_name": data["employee_name"]}


def login_as(employee_name, password, timeout=5):
    """Sign in as a *different* employee than whoever this machine is
    currently bound to, scoped to the same organization this machine
    already belongs to (not a global lookup -- see the backend endpoint's
    own docstring for why)."""
    organization_id = get_active_organization_id()
    if organization_id is None:
        return {"success": False, "error": "This machine hasn't been activated yet, so there's no organization to sign into."}

    try:
        response = requests.post(
            f"{BACKEND_URL}/employees/login-by-name",
            json={"organization_id": organization_id, "employee_name": employee_name, "password": password},
            timeout=timeout,
        )
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Can't reach the monitoring server: {e}"}

    if response.status_code != 200:
        return {"success": False, "error": response.json().get("detail", f"HTTP {response.status_code}")}

    data = response.json()
    save_token(data["access_token"], data["employee_name"])
    return {"success": True, "employee_name": data["employee_name"]}
