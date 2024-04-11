from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.factory import logging
from plextraktsync.plugin import hookimpl

if TYPE_CHECKING:
    from plextraktsync.config.SyncConfig import SyncConfig
    from plextraktsync.sync.Sync import Sync
    from plextraktsync.trakt.TraktApi import TraktApi
    from plextraktsync.trakt.TraktUserListCollection import \
        TraktUserListCollection


class LikedListsPlugin:
    logger = logging.getLogger(__name__)

    def __init__(self, trakt: TraktApi):
        self.trakt = trakt

    @staticmethod
    def enabled(config: SyncConfig):
        return config.sync_liked_lists

    @classmethod
    def factory(cls, sync: Sync):
        return cls(sync.trakt)

    @hookimpl
    def init(self, trakt_lists: TraktUserListCollection, is_partial: bool):
        if is_partial:
            self.logger.warning("Partial walk, disabling liked lists updating. "
                                "Liked lists won't update because it needs full library sync.")
        else:
            trakt_lists.load_lists(self.trakt.liked_lists)
