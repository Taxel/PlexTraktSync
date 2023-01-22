import importlib


class EventFactory:
    EVENTS = {
        "account": "AccountUpdateNotification",
        "activity": "ActivityNotification",
        "backgroundProcessingQueue": "BackgroundProcessingQueueEventNotification",
        "playing": "PlaySessionStateNotification",
        "preference": "Setting",
        "progress": "ProgressNotification",
        "reachability": "ReachabilityNotification",
        "status": "StatusNotification",
        "timeline": "TimelineEntry",
        "transcodeSession.end": "TranscodeSession",
        "transcodeSession.start": "TranscodeSession",
        "transcodeSession.update": "TranscodeSession",
    }

    def __init__(self):
        self.module = importlib.import_module("plextraktsync.watch.events")

    def get_events(self, message):
        if message["size"] != 1:
            raise ValueError(f"Unexpected size: {message}")

        message_type = message["type"]
        if message_type not in self.EVENTS:
            return
        class_name = self.EVENTS[message_type]
        if class_name not in message:
            return
        for data in message[class_name]:
            event = self.create(class_name, **data)
            yield event

    def create(self, name, **kwargs):
        cls = getattr(self.module, name)
        return cls(**kwargs)
