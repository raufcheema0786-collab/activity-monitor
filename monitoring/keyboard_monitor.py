from pynput import keyboard

class KeyboardMonitor:
    def __init__(self, idle_detector):
        self.idle_detector = idle_detector
        self.listener = None

    def _on_press(self, key):
        self.idle_detector.reset_activity()

    def start(self):
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()
