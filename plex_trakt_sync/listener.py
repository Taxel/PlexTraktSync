from time import sleep

from plexapi.server import PlexServer

from plex_trakt_sync.events import EventFactory
from plex_trakt_sync.logging import logging

PLAYING = "playing"


class WebSocketListener:
    def __init__(self, plex: PlexServer, interval=1):
        self.plex = plex
        self.interval = interval
        self.event_listeners = list()
        self.event_factory = EventFactory()
        self.logger = logging.getLogger("PlexTraktSync.WebSocketListener")

    def on(self, event_type, listener, **kwargs):
        self.event_listeners.append({
            "listener": listener,
            "event_type": event_type,
            "filters": kwargs,
        })

    def dispatch(self, event):
        for listener in self.event_listeners:
            if not self.is_candidate(event, listener):
                continue

            listener["listener"](event)

    @staticmethod
    def is_candidate(event, listener):
        if not isinstance(event, listener["event_type"]):
            return False

        if listener["filters"]:
            for name, value in listener["filters"].items():
                if name not in event:
                    return False
                if event[name] not in value:
                    return False

        return True

    def listen(self):
        def handler(data):
            self.logger.debug(data)
            events = self.event_factory.get_events(data)
            for event in events:
                self.dispatch(event)

        while True:
            notifier = self.plex.startAlertListener(callback=handler)
            while notifier.is_alive():
                sleep(self.interval)

            self.logger.debug(f"Listener finished. Restarting in {self.interval}")
            sleep(self.interval)
