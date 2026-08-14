import os
import subprocess
import sys
from pathlib import Path

import webview
from activation_service import handle_activation_if_present
from auth_storage import get_active_employee_id
import employee_login_service
from storage.database import init_db
from monitoring.session_service import SessionService
from repositories.event_repository import get_events_for_session
from repositories.screenshot_repository import get_screenshots_for_session
from repositories.session_repository import get_all_sessions, get_session_by_id

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"
SRC_DIR = FRONTEND_DIR / "src"
DIST_DIR = FRONTEND_DIR / "dist"
DIST_INDEX = DIST_DIR / "index.html"

activation_result = handle_activation_if_present()
if activation_result:
    success, message = activation_result
    if success:
        print(f"Employee activated successfully: {message}")
    else:
        print(f"Activation failed: {message}")


def run_npm_command(args):
    subprocess.run(["cmd", "/c", "npm", *args], cwd=FRONTEND_DIR, check=True)


def frontend_needs_build():
    if not DIST_INDEX.exists():
        return True

    dist_mtime = DIST_INDEX.stat().st_mtime
    for path in SRC_DIR.rglob("*"):
        if path.is_file() and path.suffix in {".js", ".jsx", ".ts", ".tsx", ".css", ".html"}:
            if path.stat().st_mtime > dist_mtime:
                return True

    return False


def build_frontend():
    node_modules_dir = FRONTEND_DIR / "node_modules"
    if not node_modules_dir.exists():
        print("Installing frontend dependencies...")
        run_npm_command(["install"])

    print("Building frontend...")
    run_npm_command(["run", "build"])


if not getattr(sys, "frozen", False):
    # A packaged executable ships the built frontend/dist baked in via
    # PyInstaller's --add-data -- there's no frontend/src, no npm, and no
    # node_modules on an end user's machine to build from, so this whole
    # dev-mode auto-build check would be meaningless (or worse, error out)
    # once frozen.
    if frontend_needs_build():
        build_frontend()

init_db()
session_service = SessionService()

class Api:
    def start_work(self):
        return session_service.start_work()

    def stop_work(self):
        return session_service.stop_work()

    def get_status(self):
        return session_service.get_status()

    def get_sessions(self):
        return get_all_sessions(employee_id=get_active_employee_id())

    def get_session_details(self, session_id):
        return {
            "session": get_session_by_id(session_id),
            "events": get_events_for_session(session_id),
            "screenshots": get_screenshots_for_session(session_id),
        }

    def open_screenshot(self, path):
        os.startfile(path)
        return True

    def get_login_state(self):
        return employee_login_service.get_login_state()

    def set_password(self, password):
        return employee_login_service.set_password(password)

    def login(self, password):
        return employee_login_service.login(password)

    def login_as(self, employee_name, password):
        # A session in progress belongs to whoever was signed in before --
        # switching identity mid-session would let events/screenshots after
        # this point get attributed to the new employee under the old
        # employee's session_id. Ending it first keeps the two cleanly
        # separated.
        if session_service.current_session_id is not None:
            session_service.stop_work()
        return employee_login_service.login_as(employee_name, password)


api = Api()

window = webview.create_window(
    "Activity Monitor",
    str(DIST_INDEX),
    js_api=api,
    width=960,
    height=720,
    min_size=(720, 560),
)

webview.start()
