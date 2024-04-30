from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.factory import logging
from plextraktsync.plugin import hookimpl

if TYPE_CHECKING:
    from ..trakt.TraktUserList import TraktUserList
    from .plugin.SyncPluginInterface import Media, Sync, SyncPluginManager


class TraktListsPlugin:
    """
    Plugin handling syncing of Trakt lists.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, keep_watched: bool, trakt_lists_config=None):
        self.keep_watched = keep_watched
        self.trakt_lists = None
        self.trakt_lists_config = trakt_lists_config or {}

    @staticmethod
    def enabled(config):
        return any(
            [
                # LikedListsPlugin
                config.sync_liked_lists,
                # WatchListPlugin
                config.update_plex_wl_as_pl,
            ]
        )

    @classmethod
    def factory(cls, sync: Sync):
        return cls(
            sync.config.liked_lists_keep_watched,
            sync.config.liked_lists,
        )

    @hookimpl(trylast=True)
    def init(self, pm: SyncPluginManager, sync: Sync):
        # Skip updating lists if it's empty
        if sync.trakt_lists.is_empty:
            self.logger.warning("Disabling TraktListsPlugin: No lists to process")
            pm.unregister(self)
            return

        self.trakt_lists = sync.trakt_lists

    @hookimpl
    async def fini(self, dry_run: bool):
        if dry_run:
            return

        with measure_time("Updated Trakt Lists"):
            for tl in self.trakt_lists:
                items = tl.plex_items_sorted(self.list_keep_watched(tl))
                updated = tl.plex_list.update(items)
                if not updated:
                    continue
                self.logger.info(
                    f"Plex list {tl.title_link} ({len(tl.plex_items)} items) updated",
                    extra={"markup": True},
                )

    def list_keep_watched(self, tl: TraktUserList):
        config = self.trakt_lists_config.get(tl.name)
        if config is None:
            return self.keep_watched
        return config.get("keep_watched", self.keep_watched)

    @hookimpl
    async def walk_movie(self, movie: Media):
        if not self.keep_watched and movie.plex.is_watched:
            return

        self.trakt_lists.add_to_lists(movie)

    @hookimpl
    async def walk_episode(self, episode: Media):
        if not self.keep_watched and episode.plex.is_watched:
            return

        self.trakt_lists.add_to_lists(episode)
