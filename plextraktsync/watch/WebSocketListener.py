from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING

from plextraktsync.factory import logging
from plextraktsync.watch.EventDispatcher import EventDispatcher
from plextraktsync.watch.events import Error, ServerStarted

if TYPE_CHECKING:
    from plexapi.server import PlexServer


class WebSocketListener:
    logger = logging.getLogger(__name__)

    def __init__(self, plex: PlexServer, poll_interval=5, restart_interval=15):
        self.plex = plex
        self.poll_interval = poll_interval
        self.restart_interval = restart_interval
        self.dispatcher = EventDispatcher()

    def on(self, event_type, listener, **kwargs):
        self.dispatcher.on(event_type, listener, **kwargs)

    def listen(self):
        self.logger.info("Listening for events!")
        while True:
            notifier = self.plex.startAlertListener(callback=self.dispatcher.event_handler)
            self.dispatcher.event_handler(ServerStarted(notifier=notifier))

            while notifier.is_alive():
                sleep(self.poll_interval)

            self.dispatcher.event_handler(Error(msg="Server closed connection"))
            self.logger.error(f"Listener finished. Restarting in {self.restart_interval} seconds")
            sleep(self.restart_interval)
