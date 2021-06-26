import importlib

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
}


class Event(dict):
    def __str__(self):
        return f"{self.__class__}:{str(self.copy())}"


class AccountUpdateNotification(Event):
    pass


class ActivityNotification(Event):
    pass


class BackgroundProcessingQueueEventNotification(Event):
    pass


class PlaySessionStateNotification(Event):
    pass


class Setting(Event):
    pass


class ProgressNotification(Event):
    pass


class ReachabilityNotification(Event):
    pass


class StatusNotification(Event):
    pass


class TimelineEntry(Event):
    pass


class EventFactory:
    def __init__(self):
        self.module = importlib.import_module(self.__module__)

    def get_events(self, message):
        if message["size"] != 1:
            raise ValueError(f"Unexpected size: {message}")

        message_type = message["type"]
        if message_type not in EVENTS:
            return
        class_name = EVENTS[message_type]
        if class_name not in message:
            return
        for data in message[class_name]:
            event = self.create(class_name, **data)
            yield event

    def create(self, name, **kwargs):
        cls = getattr(self.module, name)
        return cls(**kwargs)
