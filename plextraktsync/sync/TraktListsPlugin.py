from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.factory import logging
from plextraktsync.plugin import hookimpl

if TYPE_CHECKING:
    from .plugin.SyncPluginInterface import Media, Sync, SyncPluginManager


class TraktListsPlugin:
    """
    Plugin handling syncing of Trakt lists.
    """

    logger = logging.getLogger(__name__)

    def __init__(self):
        self.trakt_lists = None

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
    def factory(cls, sync):
        return cls()

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
                updated = tl.plex_list.update(tl.plex_items_sorted)
                if not updated:
                    continue
                self.logger.info(
                    f"Plex list {tl.title_link} ({len(tl.plex_items)} items) updated",
                    extra={"markup": True},
                )

    @hookimpl
    async def walk_movie(self, movie: Media):
        self.trakt_lists.add_to_lists(movie)

    @hookimpl
    async def walk_episode(self, episode: Media):
        self.trakt_lists.add_to_lists(episode)
