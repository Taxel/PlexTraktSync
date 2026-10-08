from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from plextraktsync.factory import logging

if TYPE_CHECKING:
    from plextraktsync.media.Media import Media
    from plextraktsync.sync.plugin.SyncPluginInterface import Sync, SyncConfig
    from plextraktsync.yamtrack.YamtrackApi import YamtrackApi


class SyncYamtrackPlugin:
    logger = logging.getLogger(__name__)

    def __init__(self, config: SyncConfig, yamtrack: YamtrackApi):
        self.config = config
        self.yamtrack = yamtrack
        self.sent = 0
        self.skipped = 0
        self.unsupported = 0

    @staticmethod
    def enabled(config: SyncConfig):
        return config.sync_yamtrack_history

    @classmethod
    def factory(cls, sync: Sync):
        from plextraktsync.factory import factory

        return cls(config=sync.config, yamtrack=factory.yamtrack_api)

    async def walk_movie(self, movie: Media, dry_run: bool):
        await self.sync_history(movie, dry_run=dry_run)

    async def walk_episode(self, episode: Media, dry_run: bool):
        await self.sync_history(episode, dry_run=dry_run)

    async def fini(self, walker, dry_run: bool):
        if self.sent or self.skipped or self.unsupported:
            action = "Would sync" if dry_run else "Synced"
            self.logger.info(f"{action} Plex history to Yamtrack: {self.sent} new, {self.skipped} existing, {self.unsupported} skipped")

    async def sync_history(self, media: Media, dry_run: bool):
        tmdb_id = self.tmdb_id(media)
        if tmdb_id is None:
            self.unsupported += 1
            self.logger.warning(f"Skipping Yamtrack sync for {media.title_link}: no tmdb id available", extra={"markup": True})
            return

        plex_history = self.plex_history(media)
        if not plex_history:
            return

        if media.is_movie:
            existing = self.yamtrack.history_keys(self.yamtrack.movie_history(tmdb_id))
        elif media.is_episode:
            existing = self.yamtrack.history_keys(
                self.yamtrack.episode_history(
                    tmdb_id,
                    media.season_number,
                    media.episode_number,
                )
            )
        else:
            self.unsupported += 1
            return

        for watched_at in plex_history:
            key = self.yamtrack.normalize_datetime(watched_at)
            if key in existing:
                self.skipped += 1
                continue

            if media.is_movie:
                self.logger.info(f"Adding Plex watch to Yamtrack: {media.title_link} at {key}", extra={"markup": True})
                if not dry_run:
                    self.yamtrack.add_movie_watch(tmdb_id, watched_at)
            else:
                self.logger.info(f"Adding Plex episode watch to Yamtrack: {media.title_link} at {key}", extra={"markup": True})
                if not dry_run:
                    self.yamtrack.add_episode_watch(
                        tmdb_id,
                        media.season_number,
                        media.episode_number,
                        watched_at,
                    )
            existing.add(key)
            self.sent += 1

    @staticmethod
    def plex_history(media: Media):
        watched = []
        seen = set()
        for entry in media.plex_history():
            viewed_at = getattr(entry, "viewedAt", None)
            if not isinstance(viewed_at, datetime):
                continue
            key = viewed_at.replace(microsecond=0).isoformat()
            if key in seen:
                continue
            seen.add(key)
            watched.append(viewed_at)
        watched.sort()
        return watched

    @staticmethod
    def tmdb_id(media: Media):
        trakt = getattr(media.show, "trakt", None) if media.is_episode else getattr(media, "trakt", None)
        ids = getattr(trakt, "ids", None) or {}
        return ids.get("ids", {}).get("tmdb")
