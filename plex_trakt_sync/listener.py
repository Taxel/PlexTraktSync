from time import sleep
from plexapi.server import PlexServer

from plex_trakt_sync.logging import logging

PLAYING = "playing"


class WebSocketListener:
    def __init__(self, plex: PlexServer, interval=1):
        self.plex = plex
        self.interval = interval
        self.event_handlers = {}
        self.logger = logging.getLogger("PlexTraktSync.WebSocketListener")

    def on(self, event_name, handler):
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []

        self.event_handlers[event_name].append(handler)

    def listen(self):
        def handler(data):
            self.logger.debug(data)
            event_type = data['type']
            if event_type not in self.event_handlers:
                return

            for handler in self.event_handlers[event_type]:
                handler(data)

        while True:
            notifier = self.plex.startAlertListener(callback=handler)
            while notifier.is_alive():
                sleep(self.interval)

            self.logger.debug(f"Listener finished. Restarting in {self.interval}")
            sleep(self.interval)
