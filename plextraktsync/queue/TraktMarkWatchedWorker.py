import trakt.sync

from plextraktsync.decorators.rate_limit import rate_limit
from plextraktsync.decorators.retry import retry
from plextraktsync.decorators.time_limit import time_limit
from plextraktsync.factory import logging
from plextraktsync.trakt.PartialTraktMedia import PartialTraktMedia
from plextraktsync.util.remove_empty_values import remove_empty_values


class TraktMarkWatchedWorker:
    # Queue this Worker can handle
    QUEUE = "add_to_history"

    def __init__(self):
        self.logger = logging.getLogger("PlexTraktSync.TraktMarkWatchedWorker")

    def __call__(self, queues):
        items = queues[self.QUEUE]
        if not len(items):
            return
        self.submit(items)
        queues[self.QUEUE].clear()

    def submit(self, items):
        for (m, watched_at) in items:
            result = self.add_to_history(m, watched_at)
            result = remove_empty_values(result.copy())
            if result:
                self.logger.debug(f"Submitted add_to_history: {result}")

    @rate_limit()
    @time_limit()
    @retry()
    def add_to_history(self, m: PartialTraktMedia, watched_at: str):
        return trakt.sync.add_to_history(m, watched_at)
