from plextraktsync.factory import logging
from plextraktsync.watch.EventFactory import EventFactory
from plextraktsync.watch.events import Error


class EventDispatcher:
    def __init__(self):
        self.event_listeners = []
        self.event_factory = EventFactory()
        self.logger = logging.getLogger("PlexTraktSync.EventDispatcher")

    def on(self, event_type, listener, **kwargs):
        self.event_listeners.append(
            {
                "listener": listener,
                "event_type": event_type,
                "filters": kwargs,
            }
        )
        return self

    def event_handler(self, data):
        self.logger.debug(data)
        if isinstance(data, Error):
            return self.dispatch(data)

        events = self.event_factory.get_events(data)
        for event in events:
            self.dispatch(event)

    def dispatch(self, event):
        for listener in self.event_listeners:
            if not self.match_event(listener, event):
                continue

            try:
                listener["listener"](event)
            except Exception as e:
                self.logger.error(f"{type(e).__name__} was raised: {e}")

                import traceback
                self.logger.debug(traceback.format_tb(e.__traceback__))

    @staticmethod
    def match_filter(event, key, match):
        if not hasattr(event, key):
            return False
        value = getattr(event, key)

        # check for arrays
        if isinstance(match, list):
            return value in match

        # check for scalars
        return value == match

    def match_event(self, listener, event):
        if not isinstance(event, listener["event_type"]):
            return False

        if listener["filters"]:
            for name, value in listener["filters"].items():
                if not self.match_filter(event, name, value):
                    return False

        return True
