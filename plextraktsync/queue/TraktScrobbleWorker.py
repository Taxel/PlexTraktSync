from __future__ import annotations

from typing import TYPE_CHECKING

from trakt.errors import ConflictException, ProcessException

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
    logger = logging.getLogger(__name__)

    def __call__(self, queues):
        for name in self.QUEUES:
            items = queues[name]
            if not len(items):
                continue
            self.submit(name, items)
            queues[name].clear()

    def submit(self, name, items):
        name = name.replace("scrobble_", "")
        results = []
        for scrobbler, progress in self.normalize(items).items():
            res = self.scrobble(scrobbler, name, progress)
            results.append(res)

        if results:
            self.logger.debug(f"Submitted {name}: {results}")

    @rate_limit()
    @time_limit()
    @retry()
    def scrobble(self, scrobbler: Scrobbler, name: str, progress: float):
        method = getattr(scrobbler, name)
        try:
            return method(progress)
        except (ConflictException, ProcessException) as e:
            self.logger.error(f"{e} {e.response.text}")
            self.logger.debug(e.response.headers)

    @staticmethod
    def normalize(items: list[TraktPlayable]):
        result = {}
        for scrobbler, progress in items:
            result[scrobbler] = progress

        return result
