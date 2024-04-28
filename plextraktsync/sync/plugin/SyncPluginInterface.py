from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.plugin import hookspec

if TYPE_CHECKING:
    from plextraktsync.config.SyncConfig import SyncConfig  # noqa: F401
    from plextraktsync.media.Media import Media
    from plextraktsync.plan.Walker import Walker
    from plextraktsync.sync.plugin import SyncPluginManager
    from plextraktsync.sync.Sync import Sync


class SyncPluginInterface:
    """A hook specification namespace."""

    @hookspec
    def init(self, pm: SyncPluginManager, sync: Sync, is_partial: bool, dry_run: bool):
        """Hook called at sync process initialization"""

    @hookspec
    def fini(self, walker: Walker, dry_run: bool):
        """Hook called at sync process finalization"""

    @hookspec
    def walk_movie(self, movie: Media, dry_run: bool):
        """Hook called walk a movie media object"""

    @hookspec
    def walk_episode(self, episode: Media, dry_run: bool):
        """Hook called walk a episode media object"""
