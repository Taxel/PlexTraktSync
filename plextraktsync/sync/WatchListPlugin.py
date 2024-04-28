from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.factory import logging
from plextraktsync.plugin import hookimpl

if TYPE_CHECKING:
    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.trakt.TraktApi import TraktApi

    from .plugin.SyncPluginInterface import Media, Sync, SyncConfig, Walker


class WatchListPlugin:
    logger = logging.getLogger(__name__)

    def __init__(self, config: SyncConfig, plex: PlexApi, trakt: TraktApi):
        self.config = config
        self.plex = plex
        self.trakt = trakt

    @staticmethod
    def enabled(config: SyncConfig):
        return any([
            config.plex_to_trakt["watchlist"],
            config.trakt_to_plex["watchlist"],
        ])

    @classmethod
    def factory(cls, sync: Sync):
        return cls(
            config=sync.config,
            plex=sync.plex,
            trakt=sync.trakt,
        )

    @hookimpl
    def init(self, sync: Sync, is_partial: bool):
        if self.config.update_plex_wl_as_pl:
            if is_partial:
                self.logger.warning("Running partial library sync. "
                                    "Watchlist as playlist won't update because it needs full library sync.")
            else:
                sync.trakt_lists.add_watchlist(self.trakt.watchlist_movies)

    def fini(self, walker: Walker, dry_run: bool):
        if walker.config.walk_watchlist and self.sync_wl:
            with measure_time("Updated watchlist"):
                self.sync_watchlist(walker, dry_run=dry_run)

        if self.config.update_plex_wl_as_pl or self.config.sync_liked_lists:
            if dry_run:
                self.logger.warning("Running partial library sync. "
                                    "Liked lists won't update because it needs full library sync.")

    @cached_property
    def plex_wl(self):
        from plextraktsync.plex.PlexWatchList import PlexWatchList

        return PlexWatchList(self.plex.watchlist())

    @cached_property
    def sync_wl(self):
        return self.config.sync_wl and len(self.plex_wl) > 0

    @cached_property
    def trakt_wl(self):
        from plextraktsync.trakt.TraktWatchlist import TraktWatchList

        return TraktWatchList(self.trakt.watchlist_movies + self.trakt.watchlist_shows)

    def watchlist_sync_item(self, m: Media, dry_run: bool):
        if m.plex is None:
            if self.config.update_plex_wl:
                self.logger.info(f"Skipping {m.title_link} from Trakt watchlist because not found in Plex Discover", extra={"markup": True})
            elif self.config.update_trakt_wl:
                self.logger.info(f"Removing {m.title_link} from Trakt watchlist", extra={"markup": True})
                if not dry_run:
                    m.remove_from_trakt_watchlist()
            return

        if m in self.plex_wl:
            if m not in self.trakt_wl:
                if self.config.update_trakt_wl:
                    self.logger.info(f"Adding {m.title_link} to Trakt watchlist", extra={"markup": True})
                    if not dry_run:
                        m.add_to_trakt_watchlist()
                else:
                    self.logger.info(f"Removing {m.title_link} from Plex watchlist", extra={"markup": True})
                    if not dry_run:
                        m.remove_from_plex_watchlist()
            else:
                # Plex Online search is inaccurate, and it doesn't offer search by id.
                # Remove known match from trakt watchlist, so that the search would not be attempted.
                # Example, trakt id 187634 where title mismatches:
                #  - "The Vortex": https://trakt.tv/movies/the-vortex-2012
                #  - "Big Bad Bugs": https://app.plex.tv/desktop/#!/provider/tv.plex.provider.vod/details?key=%2Flibrary%2Fmetadata%2F5d776b1cad5437001f7936f4
                del self.trakt_wl[m]
        elif m in self.trakt_wl:
            if self.config.update_plex_wl:
                self.logger.info(f"Adding {m.title_link} to Plex watchlist", extra={"markup": True})
                if not dry_run:
                    m.add_to_plex_watchlist()
            else:
                self.logger.info(f"Removing {m.title_link} from Trakt watchlist", extra={"markup": True})
                if not dry_run:
                    m.remove_from_trakt_watchlist()

    def sync_watchlist(self, walker: Walker, dry_run: bool):
        # NOTE: Plex watchlist sync removes matching items from trakt lists
        # See the comment above around "del self.trakt_wl[m]"
        for m in walker.media_from_plexlist(self.plex_wl):
            self.watchlist_sync_item(m, dry_run)

        # Because Plex syncing might have emptied the watchlists, skip printing the 0/0 progress
        if len(self.trakt_wl):
            for m in walker.media_from_traktlist(self.trakt_wl):
                self.watchlist_sync_item(m, dry_run)
