import time
import threading
import os
from datetime import datetime
import mss

class ScreenshotService:
    def __init__(self, dispatcher, save_folder="screenshots", interval=30):
        self.dispatcher = dispatcher
        self.save_folder = save_folder
        self.interval = interval
        self.running = False
        os.makedirs(self.save_folder, exist_ok=True)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            time.sleep(self.interval)
            if not self.running:
                break
            self._capture()

    def _capture(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.save_folder}/screenshot_{timestamp}.png"
        with mss.mss() as sct:
            sct.shot(output=filename)
        self.dispatcher.dispatch("Screenshot Taken", {"path": filename})
