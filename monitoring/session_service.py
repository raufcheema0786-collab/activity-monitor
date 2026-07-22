from datetime import datetime
from monitoring.event_dispatcher import EventDispatcher
from monitoring.idle_detector import IdleDetector
from monitoring.keyboard_monitor import KeyboardMonitor
from monitoring.mouse_monitor import MouseMonitor
from monitoring.screenshot_service import ScreenshotService
from repositories.session_repository import create_session, end_session
from repositories.event_repository import save_event
from repositories.screenshot_repository import save_screenshot
from services.session_statistics_service import calculate_statistics

class SessionService:
    def __init__(self):
        self.dispatcher = EventDispatcher()
        self.idle_detector = IdleDetector(self.dispatcher)
        self.keyboard_monitor = KeyboardMonitor(self.idle_detector)
        self.mouse_monitor = MouseMonitor(self.idle_detector)
        self.screenshot_service = ScreenshotService(self.dispatcher)
        self.dispatcher.subscribe(self._handle_event)
        self.current_session_id = None

    def _handle_event(self, event_type, metadata=None):
        if not self.current_session_id:
            return
        save_event(self.current_session_id, event_type, metadata)
        if event_type == "Screenshot Taken" and metadata:
            save_screenshot(self.current_session_id, metadata["path"])

    def start_work(self):
        self.current_session_id = create_session(datetime.now().isoformat())
        self.dispatcher.dispatch("Session Started")
        self.idle_detector.start()
        self.keyboard_monitor.start()
        self.mouse_monitor.start()
        self.screenshot_service.start()
        return self.current_session_id

    def stop_work(self):
        if not self.current_session_id:
            return None
        self.dispatcher.dispatch("Session Ended")
        self.idle_detector.stop()
        self.keyboard_monitor.stop()
        self.mouse_monitor.stop()
        self.screenshot_service.stop()
        stats = calculate_statistics(self.current_session_id)
        end_session(self.current_session_id, datetime.now().isoformat(), stats)
        finished_id = self.current_session_id
        self.current_session_id = None
        return finished_id
