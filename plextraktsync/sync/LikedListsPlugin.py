from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.factory import logging
from plextraktsync.plugin import hookimpl

if TYPE_CHECKING:
    from plextraktsync.trakt.TraktApi import TraktApi

    from .plugin.SyncPluginInterface import Sync, SyncConfig


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
    def init(self, sync: Sync, is_partial: bool, dry_run: bool):
        if is_partial or dry_run:
            self.logger.warning(
                "Partial walk, disabling liked lists updating. "
                "Liked lists won't update because it needs full library sync."
            )
        if is_partial:
            return

        sync.trakt_lists.load_lists(self.trakt.liked_lists)
