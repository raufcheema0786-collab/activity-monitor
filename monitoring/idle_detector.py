import time
import threading

class IdleDetector:
    def __init__(self, dispatcher, idle_threshold=30):
        self.dispatcher = dispatcher
        self.idle_threshold = idle_threshold
        self.last_activity = time.time()
        self.is_idle = False
        self.running = False

    def reset_activity(self):
        self.last_activity = time.time()
        if self.is_idle:
            self.is_idle = False
            self.dispatcher.dispatch("Active Again")

    def start(self):
        self.running = True
        self.last_activity = time.time()
        self.thread = threading.Thread(target=self._watch, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _watch(self):
        while self.running:
            if not self.is_idle and (time.time() - self.last_activity) >= self.idle_threshold:
                self.is_idle = True
                self.dispatcher.dispatch("Idle Started")
            time.sleep(1)
