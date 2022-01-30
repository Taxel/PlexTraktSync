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
    "transcodeSession.end": "TranscodeSession",
    "transcodeSession.start": "TranscodeSession",
    "transcodeSession.update": "TranscodeSession",
}


class Event(dict):
    def __str__(self):
        return f"{self.__class__}:{str(self.copy())}"


class Error(Event):
    @property
    def msg(self):
        return self["msg"]


class AccountUpdateNotification(Event):
    pass


class ActivityNotification(Event):
    @property
    def type(self):
        return self["Activity"]["type"]

    @property
    def progress(self):
        return self["Activity"]["progress"]

    @property
    def key(self):
        return self["Activity"]["Context"]["key"]

    @property
    def event(self):
        return self["event"]


class BackgroundProcessingQueueEventNotification(Event):
    pass


class PlaySessionStateNotification(Event):
    @property
    def key(self):
        return self["key"]

    @property
    def view_offset(self):
        return self["viewOffset"]

    @property
    def state(self):
        return self["state"]

    @property
    def session_key(self):
        return self["sessionKey"]


class Setting(Event):
    pass


class ProgressNotification(Event):
    pass


class ReachabilityNotification(Event):
    pass


class StatusNotification(Event):
    pass


class TimelineEntry(Event):
    @property
    def state(self):
        return self["state"]

    @property
    def item_id(self):
        return int(self["itemID"])

    @property
    def metadata_state(self):
        return self["metadataState"]

    @property
    def title(self):
        return self["title"]


class TranscodeSession(Event):
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
