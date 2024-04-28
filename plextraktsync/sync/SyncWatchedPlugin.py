from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.factory import logging
from plextraktsync.plugin import hookimpl

if TYPE_CHECKING:
    from .plugin.SyncPluginInterface import Media, Sync, SyncConfig


class SyncWatchedPlugin:
    logger = logging.getLogger(__name__)

    def __init__(self, config: SyncConfig):
        self.plex_to_trakt = config.plex_to_trakt["watched_status"]
        self.trakt_to_plex = config.trakt_to_plex["watched_status"]

    @staticmethod
    def enabled(config: SyncConfig):
        return config.sync_watched_status

    @classmethod
    def factory(cls, sync: Sync):
        return cls(config=sync.config)

    @hookimpl
    def walk_movie(self, movie: Media, dry_run: bool):
        self.sync_watched(movie, dry_run=dry_run)

    @hookimpl
    def walk_episode(self, episode: Media, dry_run: bool):
        self.sync_watched(episode, dry_run=dry_run)

    def sync_watched(self, m: Media, dry_run: bool):
        if m.watched_on_plex is m.watched_on_trakt:
            return

        if m.watched_on_plex:
            if not self.plex_to_trakt:
                return

            if m.is_episode and m.watched_before_reset:
                show = m.plex.item.show()
                self.logger.info(f"Show '{show.title}' has been reset in trakt at {m.show_reset_at}.")
                self.logger.info(f"Marking '{show.title}' as unwatched in Plex.")
                if not dry_run:
                    m.reset_show()
            else:
                self.logger.info(f"Marking as watched in Trakt: {m.title_link}", extra={"markup": True})
                if not dry_run:
                    m.mark_watched_trakt()
        elif m.watched_on_trakt:
            if not self.trakt_to_plex:
                return
            self.logger.info(f"Marking as watched in Plex: {m.title_link}", extra={"markup": True})
            if not dry_run:
                m.mark_watched_plex()
