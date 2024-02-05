from collections import defaultdict

import trakt.sync

from plextraktsync.decorators.rate_limit import rate_limit
from plextraktsync.decorators.retry import retry
from plextraktsync.decorators.time_limit import time_limit
from plextraktsync.factory import logging
from plextraktsync.util.remove_empty_values import remove_empty_values


class TraktBatchWorker:
    # Queues this Worker can handle
    QUEUES = (
        "add_to_collection",
        "remove_from_collection",
        "add_to_watchlist",
        "remove_from_watchlist",
    )

    def __init__(self):
        self.logger = logging.getLogger("PlexTraktSync.TraktBatchWorker")

    def __call__(self, queues):
        for name in self.QUEUES:
            items = queues[name]
            if not len(items):
                continue
            self.submit(name, items)
            queues[name].clear()

    def submit(self, name, items):
        method = getattr(self, name)
        result = method(self.normalize(items))
        result = remove_empty_values(result.copy())
        if result:
            self.logger.debug(f"Submitted {name}: {result}")

    @rate_limit()
    @time_limit()
    @retry()
    def add_to_collection(self, items):
        return trakt.sync.add_to_collection(items)

    @rate_limit()
    @time_limit()
    @retry()
    def remove_from_collection(self, items):
        return trakt.sync.remove_from_collection(items)

    @rate_limit()
    @time_limit()
    @retry()
    def add_to_watchlist(self, items):
        return trakt.sync.add_to_watchlist(items)

    @rate_limit()
    @time_limit()
    @retry()
    def remove_from_watchlist(self, items):
        return trakt.sync.remove_from_watchlist(items)

    @staticmethod
    def normalize(items):
        result = defaultdict(list)
        for media_type, item in items:
            result[media_type].append(item)

        return result
