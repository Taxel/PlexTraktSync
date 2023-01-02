from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.factory import logging

if TYPE_CHECKING:
    from trakt.sync import Scrobbler


class ScrobblerProxy:
    """
    Proxy to Scrobbler that handles requests cache and rate limiting
    """

    def __init__(self, scrobbler: Scrobbler, threshold=80):
        self.scrobbler = scrobbler
        self.threshold = threshold
        self.logger = logging.getLogger("PlexTraktSync.ScrobblerProxy")

    def update(self, progress: float):
        self.logger.debug(f"update({self.scrobbler.media}): {progress}")
        return self.scrobbler.update(progress)

    def pause(self, progress: float):
        self.logger.debug(f"pause({self.scrobbler.media}): {progress}")
        return self.scrobbler.pause(progress)

    def stop(self, progress: float):
        if progress >= self.threshold:
            self.logger.debug(f"stop({self.scrobbler.media}): {progress}")
            return self.scrobbler.stop(progress)
        else:
            self.logger.debug(f"pause({self.scrobbler.media}): {progress}")
            return self.scrobbler.pause(progress)
