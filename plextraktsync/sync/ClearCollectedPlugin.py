from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from plextraktsync.factory import logging
from plextraktsync.media.Media import Media
from plextraktsync.plugin import hookimpl

if TYPE_CHECKING:
    from plextraktsync.config.SyncConfig import SyncConfig
    from plextraktsync.sync.Sync import Sync
    from plextraktsync.trakt.TraktApi import TraktApi
    from plextraktsync.trakt.types import TraktMedia


class ClearCollectedPlugin:
    logger = logging.getLogger(__name__)

    def __init__(self, trakt: TraktApi):
        self.trakt = trakt
        self.episode_trakt_ids = set()
        self.movie_trakt_ids = set()
        self.is_partial = None

    @staticmethod
    def enabled(config: SyncConfig):
        return config.clear_collected

    @classmethod
    def factory(cls, sync: Sync):
        return cls(sync.trakt)

    @hookimpl
    def init(self, is_partial: bool):
        self.is_partial = is_partial
        if is_partial:
            self.logger.warning("Running partial library sync. Clear collected will be disabled.")

    @hookimpl
    def fini(self, dry_run: bool):
        if self.is_partial:
            return

        self.clear_collected(self.trakt.movie_collection, self.movie_trakt_ids, dry_run=dry_run)
        self.clear_collected(self.trakt.episodes_collection, self.episode_trakt_ids, dry_run=dry_run)

    @hookimpl
    def walk_movie(self, movie: Media):
        if self.is_partial:
            return

        self.movie_trakt_ids.add(movie.trakt_id)

    def clear_collected(self, existing_items: Iterable[TraktMedia], keep_ids: set[int], dry_run):
        from plextraktsync.trakt.trakt_set import trakt_set

        existing_ids = trakt_set(existing_items)
        delete_ids = existing_ids - keep_ids
        delete_items = (tm for tm in existing_items if tm.trakt in delete_ids)

        n = len(delete_ids)
        for i, tm in enumerate(delete_items, start=1):
            self.logger.info(f"Remove from Trakt collection ({i}/{n}): {tm}")
            if not dry_run:
                self.trakt.remove_from_collection(tm)
