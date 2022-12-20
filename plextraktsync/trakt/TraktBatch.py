from __future__ import annotations

import atexit
from collections import defaultdict
from typing import TYPE_CHECKING

import trakt
import trakt.movies
import trakt.sync
import trakt.users

from plextraktsync.decorators.rate_limit import rate_limit
from plextraktsync.decorators.retry import retry
from plextraktsync.decorators.time_limit import time_limit
from plextraktsync.factory import logger

if TYPE_CHECKING:
    from plextraktsync.trakt.TraktApi import TraktApi
    from plextraktsync.util.Cleanup import Cleanup


class TraktBatch:
    def __init__(self, name: str, add: bool, trakt: TraktApi, timer=None, cleanup: Cleanup = None):
        if name not in ["collection", "watchlist"]:
            raise ValueError(f"TraktBatch name not allowed: {name}")
        self.name = name
        self.add = add
        self.trakt = trakt
        self.items = defaultdict(list)
        self.timer = timer
        atexit.register(self.flush)

    @rate_limit()
    @time_limit()
    @retry()
    def submit(self):
        try:
            result = self.trakt_sync(self.items)
            result = self.remove_empty_values(result.copy())
            if result:
                logger.debug(f"Updated Trakt {self.name}: {result}")
        finally:
            self.items.clear()

    def queue_size(self):
        size = 0
        for media_type in self.items:
            size += len(self.items[media_type])

        return size

    def flush(self, force=True):
        """
        Flush the queue not sooner than seconds specified in timer
        """
        if not self.timer and force is False:
            return
        if self.queue_size() == 0:
            return

        self.timer.start()

        if not force and self.timer.time_remaining:
            return

        self.submit()
        self.timer.update()

    def add_to_items(self, media_type: str, item):
        """
        Add item of media_type to list of items
        """
        self.items[media_type].append(item)
        self.flush(force=False)

    def trakt_sync(self, media_object):
        if self.name == "collection":
            if self.add:
                return trakt.sync.add_to_collection(media_object)
            else:
                return trakt.sync.remove_from_collection(media_object)
        if self.name == "watchlist":
            if self.add:
                return trakt.sync.add_to_watchlist(media_object)
            else:
                return trakt.sync.remove_from_watchlist(media_object)

    @staticmethod
    def remove_empty_values(result):
        """
        Update result to remove empty changes.
        This makes diagnostic printing cleaner if we don't print "changed: 0"
        """
        for change_type in ["added", "existing", "updated"]:
            if change_type not in result:
                continue
            for media_type, value in result[change_type].copy().items():
                if value == 0:
                    del result[change_type][media_type]
            if len(result[change_type]) == 0:
                del result[change_type]

        for media_type, items in result["not_found"].copy().items():
            if len(items) == 0:
                del result["not_found"][media_type]

        if len(result["not_found"]) == 0:
            del result["not_found"]

        if len(result) == 0:
            return None

        return result
