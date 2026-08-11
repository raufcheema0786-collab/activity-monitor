import json
import os

SYNC_HEALTH_FILE = "sync_health.json"


def mark_sync_auth_failed():
    with open(SYNC_HEALTH_FILE, "w") as f:
        json.dump({"auth_failed": True}, f)


def clear_sync_auth_failed():
    if os.path.exists(SYNC_HEALTH_FILE):
        os.remove(SYNC_HEALTH_FILE)


def is_sync_auth_failed():
    if not os.path.exists(SYNC_HEALTH_FILE):
        return False
    with open(SYNC_HEALTH_FILE) as f:
        return json.load(f).get("auth_failed", False)
