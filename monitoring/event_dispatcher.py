class EventDispatcher:
    def __init__(self):
        self.listeners = []

    def subscribe(self, callback):
        self.listeners.append(callback)

    def dispatch(self, event_type, metadata=None):
        for callback in self.listeners:
            callback(event_type, metadata)
