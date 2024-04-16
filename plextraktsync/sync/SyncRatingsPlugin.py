from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.factory import logging
from plextraktsync.plugin import hookimpl

if TYPE_CHECKING:
    from .plugin.SyncPluginInterface import Media, Sync, SyncConfig, Walker


class SyncRatingsPlugin:
    logger = logging.getLogger(__name__)

    def __init__(self, config: SyncConfig):
        self.rating_priority = config["rating_priority"]
        self.plex_to_trakt = config.plex_to_trakt["ratings"]
        self.trakt_to_plex = config.trakt_to_plex["ratings"]
        self.shows = None

    @staticmethod
    def enabled(config: SyncConfig):
        return config.sync_ratings

    @classmethod
    def factory(cls, sync: Sync):
        return cls(config=sync.config)

    @hookimpl
    def init(self):
        self.shows = set()

    @hookimpl
    async def fini(self, walker: Walker, dry_run: bool):
        for show in walker.walk_shows(self.shows, title="Syncing show ratings"):
            self.sync_ratings(show, dry_run=dry_run)

    @hookimpl
    async def walk_movie(self, movie: Media, dry_run: bool):
        self.sync_ratings(movie, dry_run=dry_run)

    @hookimpl
    async def walk_episode(self, episode: Media, dry_run: bool):
        self.sync_ratings(episode, dry_run=dry_run)

        if episode.show:
            self.shows.add(episode.show)

    def sync_ratings(self, m: Media, dry_run: bool):
        if m.plex_rating == m.trakt_rating:
            return

        has_trakt = m.trakt_rating is not None
        has_plex = m.plex_rating is not None
        rate = None

        if self.rating_priority == "none":
            # Only rate items with missing rating
            if self.plex_to_trakt and has_plex and not has_trakt:
                rate = "trakt"
            elif self.trakt_to_plex and has_trakt and not has_plex:
                rate = "plex"

        elif self.rating_priority == "trakt":
            # If two-way rating sync, Trakt rating takes precedence over Plex rating
            if self.trakt_to_plex and has_trakt:
                rate = "plex"
            elif self.plex_to_trakt and has_plex:
                rate = "trakt"

        elif self.rating_priority == "plex":
            # If two-way rating sync, Plex rating takes precedence over Trakt rating
            if self.plex_to_trakt and has_plex:
                rate = "trakt"
            elif self.trakt_to_plex and has_trakt:
                rate = "plex"

        if rate == "trakt":
            self.logger.info(f"Rating {m.title_link} with {m.plex_rating} on Trakt (was {m.trakt_rating})", extra={"markup": True})
            if not dry_run:
                m.trakt_rate()

        elif rate == "plex":
            self.logger.info(f"Rating {m.title_link} with {m.trakt_rating} on Plex (was {m.plex_rating})", extra={"markup": True})
            if not dry_run:
                m.plex_rate()
