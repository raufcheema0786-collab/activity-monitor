import os
import subprocess
from pathlib import Path

import webview
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


if frontend_needs_build():
    build_frontend()

init_db()
session_service = SessionService()

class Api:
    def start_work(self):
        return session_service.start_work()

    def stop_work(self):
        return session_service.stop_work()

    def get_sessions(self):
        return get_all_sessions()

    def get_session_details(self, session_id):
        return {
            "session": get_session_by_id(session_id),
            "events": get_events_for_session(session_id),
            "screenshots": get_screenshots_for_session(session_id),
        }

    def open_screenshot(self, path):
        os.startfile(path)
        return True


api = Api()

window = webview.create_window(
    "Activity Monitor",
    str(DIST_INDEX),
    js_api=api,
)

webview.start()
