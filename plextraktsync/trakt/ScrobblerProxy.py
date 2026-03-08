from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.factory import factory, logging

if TYPE_CHECKING:
    from trakt.sync import Scrobbler


class ScrobblerProxy:
    """
    Proxy to Scrobbler that queues requests to update trakt
    """

    WATCHED_THRESHOLD = 80

    logger = logging.getLogger(__name__)

    def __init__(self, scrobbler: Scrobbler):
        self.scrobbler = scrobbler

    def update(self, progress: float):
        self.logger.debug(f"update({self.scrobbler.media}): {progress}")
        self.queue.scrobble_update((self.scrobbler, progress))

    def pause(self, progress: float):
        progress = max(progress, 1.0)  # Trakt requires at least 1%
        # Cap progress below WATCHED_THRESHOLD to prevent Trakt from marking
        # a paused item as watched (stop with progress >= 80% triggers a scrobble).
        progress = min(progress, self.WATCHED_THRESHOLD - 0.1)
        self.logger.debug(f"pause({self.scrobbler.media}): {progress}")
        self.queue.scrobble_stop((self.scrobbler, progress))

    def stop(self, progress: float):
        progress = max(progress, 1.0)  # Trakt requires at least 1%
        action = "stop" if progress >= self.WATCHED_THRESHOLD else "pause"
        self.logger.debug(f"{action}({self.scrobbler.media}): {progress}")
        self.queue.scrobble_stop((self.scrobbler, progress))

    @cached_property
    def queue(self):
        return factory.queue
