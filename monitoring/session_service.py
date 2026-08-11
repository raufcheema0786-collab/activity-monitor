import threading
import time
import uuid
from datetime import datetime
from monitoring.event_dispatcher import EventDispatcher
from monitoring.idle_detector import IdleDetector
from monitoring.keyboard_monitor import KeyboardMonitor
from monitoring.mouse_monitor import MouseMonitor
from monitoring.screenshot_service import ScreenshotService
from auth_storage import get_active_employee_id
from repositories.session_repository import create_session, end_session, get_session_by_id
from repositories.event_repository import save_event
from repositories.screenshot_repository import save_screenshot
from retry_service import start_retry_loop
from services.session_statistics_service import calculate_statistics, get_today_totals
from settings_storage import load_settings
from sync_service import start_remote_session, end_remote_session, send_event, send_screenshot, send_heartbeat
from sync_health import is_sync_auth_failed


def _run_in_background(fn, *args, **kwargs):
    """Fire a sync call on its own thread so a slow/unreachable backend
    never blocks the caller (keyboard/mouse listener thread, screenshot
    thread, etc). Local monitoring keeps running regardless of what the
    network is doing."""

    def _run():
        try:
            fn(*args, **kwargs)
        except Exception as e:
            print(f"[session] unexpected error in background sync call {fn.__name__}: {e}")

    threading.Thread(target=_run, daemon=True).start()


class SessionService:
    def __init__(self):
        settings = load_settings()
        self.heartbeat_interval = settings["heartbeat_interval_seconds"]
        self.heartbeat_timeout = settings["heartbeat_timeout_seconds"]
        self.heartbeat_running = False
        self.dispatcher = EventDispatcher()
        self.idle_detector = IdleDetector(self.dispatcher, idle_threshold=settings["idle_timeout_seconds"])
        self.keyboard_monitor = KeyboardMonitor(self.idle_detector)
        self.mouse_monitor = MouseMonitor(self.idle_detector)
        self.screenshot_service = ScreenshotService(self.dispatcher, interval=settings["screenshot_interval_seconds"])
        self.dispatcher.subscribe(self._handle_event)
        self.current_session_id = None
        self.remote_session_id = None
        self.session_client_ref = None
        self.last_heartbeat_at = None
        # Drains the local pending_uploads queue on its own schedule,
        # independent of whether a session is currently active.
        start_retry_loop()

    def _heartbeat_loop(self):
        while self.heartbeat_running:
            try:
                if send_heartbeat(str(uuid.uuid4()), timeout=self.heartbeat_timeout):
                    self.last_heartbeat_at = datetime.now().isoformat()
            except Exception as e:
                print(f"[session] unexpected error sending heartbeat: {e}")
            time.sleep(self.heartbeat_interval)

    def _handle_event(self, event_type, metadata=None):
        if not self.current_session_id:
            return

        employee_id = get_active_employee_id()
        timestamp = datetime.utcnow().isoformat()
        client_ref = str(uuid.uuid4())

        if event_type == "Screenshot Taken" and metadata:
            save_event(self.current_session_id, event_type, metadata, client_ref, employee_id=employee_id)
            save_screenshot(self.current_session_id, metadata["path"], client_ref, employee_id=employee_id)
            _run_in_background(
                send_screenshot, self.remote_session_id, self.session_client_ref,
                metadata["path"], timestamp, client_ref,
            )
        else:
            save_event(self.current_session_id, event_type, metadata, client_ref, employee_id=employee_id)
            _run_in_background(
                send_event, self.remote_session_id, self.session_client_ref,
                event_type, timestamp, metadata, client_ref,
            )

    def start_work(self):
        self.session_client_ref = str(uuid.uuid4())
        self.remote_session_id = start_remote_session(self.session_client_ref)
        self.current_session_id = create_session(
            datetime.now().isoformat(), self.session_client_ref, employee_id=get_active_employee_id()
        )
        self.dispatcher.dispatch("Session Started")
        self.idle_detector.start()
        self.keyboard_monitor.start()
        self.mouse_monitor.start()
        self.heartbeat_running = True
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        self.screenshot_service.start()
        return self.current_session_id

    def stop_work(self):
        if not self.current_session_id:
            return None
        self.dispatcher.dispatch("Session Ended")
        self.idle_detector.stop()
        self.keyboard_monitor.stop()
        self.heartbeat_running = False
        self.mouse_monitor.stop()
        self.screenshot_service.stop()
        end_remote_session(self.remote_session_id, self.session_client_ref)
        stats = calculate_statistics(self.current_session_id)
        end_session(self.current_session_id, datetime.now().isoformat(), stats)
        finished_id = self.current_session_id
        self.current_session_id = None
        self.remote_session_id = None
        self.session_client_ref = None
        return finished_id

    def get_status(self):
        """Read-only snapshot for the employee-facing status view. Never
        starts, stops, or otherwise changes tracking state."""
        tracking = self.current_session_id is not None
        if not tracking:
            tracking_status = "not_tracking"
        elif self.idle_detector.is_idle:
            tracking_status = "idle"
        else:
            tracking_status = "active"

        session_duration_seconds = 0
        if tracking:
            session = get_session_by_id(self.current_session_id)
            if session and session.get("start_time"):
                started = datetime.fromisoformat(session["start_time"])
                session_duration_seconds = max(0, int((datetime.now() - started).total_seconds()))

        today_active_seconds, today_idle_seconds = get_today_totals(
            get_active_employee_id(), self.current_session_id
        )

        return {
            "tracking_status": tracking_status,
            "session_duration_seconds": session_duration_seconds,
            "today_active_seconds": today_active_seconds,
            "today_idle_seconds": today_idle_seconds,
            "last_heartbeat_at": self.last_heartbeat_at,
            "sync_auth_failed": is_sync_auth_failed(),
            "settings": {
                "screenshot_interval_seconds": self.screenshot_service.interval,
                "idle_timeout_seconds": self.idle_detector.idle_threshold,
                "heartbeat_interval_seconds": self.heartbeat_interval,
            },
        }
