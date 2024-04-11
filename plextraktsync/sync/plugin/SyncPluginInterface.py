from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.plugin import hookspec

if TYPE_CHECKING:
    from plextraktsync.media.Media import Media
    from plextraktsync.plan.Walker import Walker
    from plextraktsync.sync.Sync import Sync
    from plextraktsync.trakt.TraktUserListCollection import \
        TraktUserListCollection


class SyncPluginInterface:
    """A hook specification namespace."""

    @hookspec
    def init(self, sync: Sync, trakt_lists: TraktUserListCollection, is_partial: bool, dry_run: bool):
        """Hook called at sync process initialization"""

    @hookspec
    def fini(self, walker: Walker, trakt_lists: TraktUserListCollection, dry_run: bool):
        """Hook called at sync process finalization"""

    @hookspec
    def walk_movie(self, movie: Media, dry_run: bool):
        """Hook called walk a movie media object"""

    @hookspec
    def walk_episode(self, episode: Media, dry_run: bool):
        """Hook called walk a episode media object"""
