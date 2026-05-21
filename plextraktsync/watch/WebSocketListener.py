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

    def __init__(self, plex: PlexServer, poll_interval=5, restart_interval=15, fatal_error=None):
        self.plex = plex
        self.poll_interval = poll_interval
        self.restart_interval = restart_interval
        self.fatal_error = fatal_error
        self.dispatcher = EventDispatcher(fatal_error=fatal_error)

    def on(self, event_type, listener, **kwargs):
        self.dispatcher.on(event_type, listener, **kwargs)

    def listen(self):
        self.logger.info("Listening for events!")
        while True:
            if self.fatal_error is not None:
                self.fatal_error.raise_if_set()

            notifier = self.plex.startAlertListener(callback=self.dispatcher.event_handler)
            self.dispatcher.event_handler(ServerStarted(notifier=notifier))

            while notifier.is_alive():
                sleep(self.poll_interval)
                if self.fatal_error is not None:
                    self.fatal_error.raise_if_set()

            self.dispatcher.event_handler(Error(msg="Server closed connection"))
            self.logger.error(f"Listener finished. Restarting in {self.restart_interval} seconds")
            sleep(self.restart_interval)
