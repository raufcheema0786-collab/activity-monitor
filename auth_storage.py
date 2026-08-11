import base64
import json
import os

TOKEN_FILE = "auth_token.json"


def _decode_employee_id(access_token):
    """Read the employee_id claim straight out of the JWT payload, without
    verifying the signature -- this is only ever used as a local scoping
    tag for monitor.db, not for authentication (the token itself, sent
    as-is in the Authorization header, is what the backend verifies)."""
    try:
        payload_segment = access_token.split(".")[1]
        padding = "=" * (-len(payload_segment) % 4)
        decoded = base64.urlsafe_b64decode(payload_segment + padding)
        return json.loads(decoded).get("employee_id")
    except Exception:
        return None


def save_token(access_token, employee_name):
    with open(TOKEN_FILE, "w") as f:
        json.dump(
            {
                "access_token": access_token,
                "employee_name": employee_name,
                "employee_id": _decode_employee_id(access_token),
            },
            f,
        )


def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        return json.load(f)


def is_authenticated():
    return load_token() is not None


def get_active_employee_id():
    token_data = load_token()
    if not token_data:
        return None
    return token_data.get("employee_id")
