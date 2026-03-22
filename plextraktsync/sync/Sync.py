from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.factory import logging
from plextraktsync.trakt.TraktUserListCollection import TraktUserListCollection
from plextraktsync.trakt.TraktWatchedCollection import TraktWatchedCollection

if TYPE_CHECKING:
    from plextraktsync.config.SyncConfig import SyncConfig
    from plextraktsync.plan.Walker import Walker
    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.trakt.TraktApi import TraktApi


class Sync:
    logger = logging.getLogger(__name__)

    def __init__(self, config: SyncConfig, plex: PlexApi, trakt: TraktApi):
        self.config = config
        self.plex = plex
        self.trakt = trakt
        self.walker = None

    @cached_property
    def trakt_lists(self):
        return TraktUserListCollection(
            self.config.liked_lists_keep_watched,
            self.config.liked_lists_overrides,
        )

    @cached_property
    def pm(self):
        from .plugin import SyncPluginManager

        pm = SyncPluginManager()
        pm.register_plugins(self)

        return pm

    async def sync(self, walker: Walker, dry_run=False):
        self.walker = walker
        is_partial = walker.is_partial

        pm = self.pm
        pm.hook.init(sync=self, pm=pm, is_partial=is_partial, dry_run=dry_run)

        if self.config.need_library_walk:
            async for movie in walker.find_movies():
                await pm.ahook.walk_movie(movie=movie, dry_run=dry_run)

            async for episode in walker.find_episodes():
                await pm.ahook.walk_episode(episode=episode, dry_run=dry_run)

        if self.config.plex_online:
            await self.sync_online(dry_run)

        await pm.ahook.fini(walker=walker, dry_run=dry_run)

    async def sync_online(self, dry_run: bool):
        """
        Sync watched status from Trakt to Plex Discover (cloud items)
        """
        logger = logging.getLogger(__name__)
        logger.info("Syncing watched status with Plex Discover")

        try:
            watched_collection = TraktWatchedCollection(self.trakt)
        except Exception as e:
            logger.error(f"Failed to fetch watched collection from Trakt: {e}")
            return

        for media_type in ["movies", "episodes"]:
            watched_items = watched_collection[media_type]
            logger.info(f"Processing {len(watched_items)} watched {media_type}")

            trakt_items = list(watched_items.values())
            async for m in self.walker.media_from_traktlist(trakt_items):
                if not m.plex or not m.plex.is_discover:
                    if not m.plex:
                        logger.warning(f"Could not resolve {m.trakt_item} in Plex Discover")
                    continue  # Skip if not in discover

                # Sync watched status from Trakt to Plex
                if not m.watched_on_plex and m.watched_on_trakt:
                    logger.info(f"Marking {m} as watched on Plex")
                    if not dry_run:
                        try:
                            m.mark_watched_plex()
                        except Exception as e:
                            logger.error(f"Failed to mark {m} as watched on Plex: {e}")
                            # Continue processing other items
