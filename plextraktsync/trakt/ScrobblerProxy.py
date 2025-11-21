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

    logger = logging.getLogger(__name__)

    def __init__(self, scrobbler: Scrobbler, threshold=80):
        self.scrobbler = scrobbler
        self.threshold = threshold

    def update(self, progress: float):
        self.logger.debug(f"update({self.scrobbler.media}): {progress}")
        self.queue.scrobble_update((self.scrobbler, progress))

    def pause(self, progress: float):
        if progress < 1:  # Trakt requires pause to be at least 1%
            progress = 1.0
        self.logger.debug(f"pause({self.scrobbler.media}): {progress}")
        self.queue.scrobble_pause((self.scrobbler, progress))

    def stop(self, progress: float):
        if progress >= self.threshold:
            self.logger.debug(f"stop({self.scrobbler.media}): {progress}")
            self.queue.scrobble_stop((self.scrobbler, progress))
        else:
            if progress < 1:  # Trakt requires pause to be at least 1%
                progress = 1.0
            self.logger.debug(f"pause({self.scrobbler.media}): {progress}")
            self.queue.scrobble_pause((self.scrobbler, progress))

    @cached_property
    def queue(self):
        return factory.queue
