import json
import os

SETTINGS_FILE = "app_settings.json"

DEFAULT_SETTINGS = {
    "screenshot_interval_seconds": 30,
    "idle_timeout_seconds": 30,
    "heartbeat_interval_seconds": 30,
    "heartbeat_timeout_seconds": 5,
}


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return dict(DEFAULT_SETTINGS)
    with open(SETTINGS_FILE) as f:
        stored = json.load(f)
    return {**DEFAULT_SETTINGS, **stored}
