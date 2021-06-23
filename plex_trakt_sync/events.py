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


class EventFactory:
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
            event = self.create(cls=class_name, **data)
            yield event

    @staticmethod
    def create(cls, **kwargs):
        # https://stackoverflow.com/a/2827726/2314626
        return type(cls, (object,), kwargs)
