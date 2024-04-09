from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.factory import logging
from plextraktsync.trakt.TraktUserListCollection import TraktUserListCollection

if TYPE_CHECKING:
    from plextraktsync.config.SyncConfig import SyncConfig
    from plextraktsync.media.Media import Media
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

    def sync(self, walker: Walker, dry_run=False):
        self.walker = walker
        trakt_lists = TraktUserListCollection()
        is_partial = walker.is_partial and not dry_run

        from plextraktsync.sync.plugin import SyncPluginManager
        pm = SyncPluginManager()
        pm.register_plugins(self)

        pm.hook.init(sync=self, trakt_lists=trakt_lists, is_partial=is_partial, dry_run=dry_run)

        if self.config.update_plex_wl_as_pl:
            if is_partial:
                self.logger.warning("Running partial library sync. Watchlist as playlist won't update because it needs full library sync.")
            else:
                trakt_lists.add_watchlist(self.trakt.watchlist_movies)

        # Skip updating lists if it's empty
        add_to_lists = not trakt_lists.is_empty

        if self.config.need_library_walk:
            for movie in walker.find_movies():
                pm.hook.walk_movie(movie=movie, dry_run=dry_run)
                if add_to_lists:
                    trakt_lists.add_to_lists(movie)

            for episode in walker.find_episodes():
                pm.hook.walk_episode(episode=episode, dry_run=dry_run)
                if add_to_lists:
                    trakt_lists.add_to_lists(episode)

        if self.config.update_plex_wl_as_pl or self.config.sync_liked_lists:
            if not add_to_lists:
                self.logger.warning("Running partial library sync. Liked lists won't update because it needs full library sync.")
            else:
                if not dry_run:
                    with measure_time("Updated liked list"):
                        trakt_lists.sync()

        if walker.config.walk_watchlist and self.sync_wl:
            with measure_time("Updated watchlist"):
                self.sync_watchlist(walker, dry_run=dry_run)

        pm.hook.fini(walker=walker, trakt_lists=trakt_lists, dry_run=dry_run)

    def watchlist_sync_item(self, m: Media, dry_run=False):
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

    def sync_watchlist(self, walker: Walker, dry_run=False):
        # NOTE: Plex watchlist sync removes matching items from trakt lists
        # See the comment above around "del self.trakt_wl[m]"
        for m in walker.media_from_plexlist(self.plex_wl):
            self.watchlist_sync_item(m, dry_run)

        # Because Plex syncing might have emptied the watchlists, skip printing the 0/0 progress
        if len(self.trakt_wl):
            for m in walker.media_from_traktlist(self.trakt_wl):
                self.watchlist_sync_item(m, dry_run)
