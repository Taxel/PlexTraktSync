from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.rate_limit import rate_limit
from plextraktsync.decorators.retry import retry
from plextraktsync.decorators.time_limit import time_limit
from plextraktsync.factory import logging

if TYPE_CHECKING:
    from trakt.sync import Scrobbler

    from plextraktsync.trakt.types import TraktPlayable


class TraktScrobbleWorker:
    # Queues this Worker can handle
    QUEUES = (
        "scrobble_update",
        "scrobble_pause",
        "scrobble_stop",
    )

    def __init__(self):
        self.logger = logging.getLogger("PlexTraktSync.TraktScrobbleWorker")

    def __call__(self, queues):
        for name in self.QUEUES:
            items = queues[name]
            if not len(items):
                continue
            self.submit(name, items)
            queues[name].clear()

    def submit(self, name, items):
        method = getattr(self, name)
        results = []
        for scrobbler, progress in self.normalize(items).items():
            res = method(scrobbler, progress)
            results.append(res)

        if results:
            self.logger.debug(f"Submitted {name}: {results}")

    @rate_limit()
    @time_limit()
    @retry()
    def scrobble_update(self, scrobbler: Scrobbler, progress: float):
        return scrobbler.update(progress)

    @rate_limit()
    @time_limit()
    @retry()
    def scrobble_pause(self, scrobbler: Scrobbler, progress: float):
        return scrobbler.update(progress)

    @rate_limit()
    @time_limit()
    @retry()
    def scrobble_stop(self, scrobbler: Scrobbler, progress: float):
        return scrobbler.stop(progress)

    @staticmethod
    def normalize(items: list[TraktPlayable]):
        result = {}
        for (scrobbler, progress) in items:
            result[scrobbler] = progress

        return result
