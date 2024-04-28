from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from plextraktsync.factory import logging
from plextraktsync.media.Media import Media
from plextraktsync.plugin import hookimpl

if TYPE_CHECKING:
    from plextraktsync.trakt.TraktApi import TraktApi

    from .plugin.SyncPluginInterface import Sync, SyncConfig


class WatchProgressPlugin:
    logger = logging.getLogger(__name__)

    def __init__(self, trakt: TraktApi):
        self.trakt = trakt

    @staticmethod
    def enabled(config: SyncConfig):
        return config.sync_playback_status

    @classmethod
    def factory(cls, sync: Sync):
        return cls(sync.trakt)

    @hookimpl
    def walk_movie(self, movie: Media, dry_run: bool):
        self.sync_progress(movie, dry_run=dry_run)

    @hookimpl
    def walk_episode(self, episode: Media, dry_run: bool):
        self.sync_progress(episode, dry_run=dry_run)

    def sync_progress(self, m: Media, dry_run=False):
        p = self.trakt.watch_progress.match(m)
        if not p:
            return
        progress = m.plex.progress_millis(p.progress)
        if progress == 0.0:
            self.logger.warning(f"{m.title_link}: Skip progress, setting to 0 will not work", extra={"markup": True})
            return

        view_offset = timedelta(milliseconds=m.plex.item.viewOffset)
        progress_offset = timedelta(milliseconds=progress)
        self.logger.info(
            f"{m.title_link}: Set watch progress to {p.progress:.02F}%: {view_offset} -> {progress_offset}",
            extra={"markup": True}
        )
        if not dry_run:
            m.plex.item.updateProgress(progress)
