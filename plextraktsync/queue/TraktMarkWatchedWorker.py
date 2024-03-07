from __future__ import annotations

from collections import defaultdict

import trakt.sync

from plextraktsync.decorators.rate_limit import rate_limit
from plextraktsync.decorators.retry import retry
from plextraktsync.decorators.time_limit import time_limit
from plextraktsync.factory import logging
from plextraktsync.util.remove_empty_values import remove_empty_values


class TraktMarkWatchedWorker:
    # Queue this Worker can handle
    QUEUE = "add_to_history"
    logger = logging.getLogger(__name__)

    def __call__(self, queues):
        items = queues[self.QUEUE]
        if not len(items):
            return
        self.submit(items)
        queues[self.QUEUE].clear()

    def submit(self, items):
        items = self.normalize(items)
        self.logger.debug(f"Submit add_to_history: {items}")
        result = self.add_to_history(items)
        result = remove_empty_values(result.copy())
        if result:
            self.logger.debug(f"Submitted add_to_history: {result}")

    @rate_limit()
    @time_limit()
    @retry()
    def add_to_history(self, items: dict):
        return trakt.sync.add_to_history(items)

    @staticmethod
    def normalize(items: list):
        result = defaultdict(list)
        for m in items:
            result[m.media_type].append({
                "ids": m.ids["ids"],
                "watched_at": m.watched_at,
            })

        return result
