from pynput import mouse

class MouseMonitor:
    def __init__(self, idle_detector):
        self.idle_detector = idle_detector
        self.listener = None

    def _on_move(self, x, y):
        self.idle_detector.reset_activity()

    def _on_click(self, x, y, button, pressed):
        self.idle_detector.reset_activity()

    def start(self):
        self.listener = mouse.Listener(on_move=self._on_move, on_click=self._on_click)
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()
