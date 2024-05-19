from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.factory import logging
from plextraktsync.plugin import hookimpl

if TYPE_CHECKING:
    from .plugin.SyncPluginInterface import Media, SyncConfig


class AddCollectionPlugin:
    logger = logging.getLogger(__name__)

    @staticmethod
    def enabled(config: SyncConfig):
        return config.plex_to_trakt["collection"]

    @classmethod
    def factory(cls, sync):
        return cls()

    @hookimpl
    async def walk_movie(self, movie: Media, dry_run: bool):
        await self.sync_collection(movie, dry_run=dry_run)

    @hookimpl
    async def walk_episode(self, episode: Media, dry_run: bool):
        await self.sync_collection(episode, dry_run=dry_run)

    async def sync_collection(self, m: Media, dry_run: bool):
        if m.is_collected:
            return

        self.logger.info(
            f"Adding to Trakt collection: {m.title_link}", extra={"markup": True}
        )

        if not dry_run:
            m.add_to_collection()
