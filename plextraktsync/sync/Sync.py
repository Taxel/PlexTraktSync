from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.factory import logging
from plextraktsync.trakt.TraktUserListCollection import TraktUserListCollection

if TYPE_CHECKING:
    from typing import Iterable

    from plextraktsync.config.SyncConfig import SyncConfig
    from plextraktsync.media.Media import Media
    from plextraktsync.plan.Walker import Walker
    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.trakt.TraktApi import TraktApi
    from plextraktsync.trakt.types import TraktMedia


class Sync:
    logger = logging.getLogger(__name__)

    def __init__(self, config: SyncConfig, plex: PlexApi, trakt: TraktApi):
        self.config = config
        self.plex = plex
        self.trakt = trakt

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
        trakt_lists = TraktUserListCollection()
        is_partial = walker.is_partial and not dry_run

        if is_partial and self.config.clear_collected:
            self.logger.warning("Running partial library sync. Clear collected will be disabled.")

        if self.config.update_plex_wl_as_pl:
            if is_partial:
                self.logger.warning("Running partial library sync. Watchlist as playlist won't update because it needs full library sync.")
            else:
                trakt_lists.add_watchlist(self.trakt.watchlist_movies)

        if self.config.sync_liked_lists:
            if is_partial:
                self.logger.warning("Partial walk, disabling liked lists updating. Liked lists won't update because it needs full library sync.")
            else:
                trakt_lists.load_lists(self.trakt.liked_lists)

        if self.config.need_library_walk:
            movie_trakt_ids = set()
            for movie in walker.find_movies():
                self.sync_collection(movie, dry_run=dry_run)
                self.sync_ratings(movie, dry_run=dry_run)
                self.sync_watched(movie, dry_run=dry_run)
                if not is_partial:
                    trakt_lists.add_to_lists(movie)
                    if self.config.clear_collected:
                        movie_trakt_ids.add(movie.trakt_id)

            if movie_trakt_ids:
                self.clear_collected(self.trakt.movie_collection, movie_trakt_ids)

            shows = set()
            episode_trakt_ids = set()
            for episode in walker.find_episodes():
                self.sync_collection(episode, dry_run=dry_run)
                self.sync_ratings(episode, dry_run=dry_run)
                self.sync_watched(episode, dry_run=dry_run)
                if not is_partial:
                    trakt_lists.add_to_lists(episode)
                    if self.config.clear_collected:
                        episode_trakt_ids.add(episode.trakt_id)

                if self.config.sync_ratings and episode.show:
                    # collect shows for later ratings sync
                    shows.add(episode.show)

            if episode_trakt_ids:
                self.clear_collected(self.trakt.episodes_collection, episode_trakt_ids)

            for show in walker.walk_shows(shows, title="Syncing show ratings"):
                self.sync_ratings(show, dry_run=dry_run)

        if self.config.update_plex_wl_as_pl or self.config.sync_liked_lists:
            if is_partial:
                self.logger.warning("Running partial library sync. Liked lists won't update because it needs full library sync.")
            else:
                if not dry_run:
                    with measure_time("Updated liked list"):
                        trakt_lists.sync()

        if walker.config.walk_watchlist and self.sync_wl:
            with measure_time("Updated watchlist"):
                self.sync_watchlist(walker, dry_run=dry_run)

    def sync_collection(self, m: Media, dry_run=False):
        if not self.config.plex_to_trakt["collection"]:
            return

        if m.is_collected:
            return

        self.logger.info(f"Adding to Trakt collection: {m.title_link}", extra={"markup": True})

        if not dry_run:
            m.add_to_collection()

    def sync_ratings(self, m: Media, dry_run=False):
        if not self.config.sync_ratings:
            return

        if m.plex_rating == m.trakt_rating:
            return

        rating_priority = self.config["rating_priority"]
        plex_to_trakt = self.config.plex_to_trakt["ratings"]
        trakt_to_plex = self.config.trakt_to_plex["ratings"]
        has_trakt = m.trakt_rating is not None
        has_plex = m.plex_rating is not None
        rate = None

        if rating_priority == "none":
            # Only rate items with missing rating
            if plex_to_trakt and has_plex and not has_trakt:
                rate = "trakt"
            elif trakt_to_plex and has_trakt and not has_plex:
                rate = "plex"

        elif rating_priority == "trakt":
            # If two-way rating sync, Trakt rating takes precedence over Plex rating
            if trakt_to_plex and has_trakt:
                rate = "plex"
            elif plex_to_trakt and has_plex:
                rate = "trakt"

        elif rating_priority == "plex":
            # If two-way rating sync, Plex rating takes precedence over Trakt rating
            if plex_to_trakt and has_plex:
                rate = "trakt"
            elif trakt_to_plex and has_trakt:
                rate = "plex"

        if rate == "trakt":
            self.logger.info(f"Rating {m.title_link} with {m.plex_rating} on Trakt (was {m.trakt_rating})", extra={"markup": True})
            if not dry_run:
                m.trakt_rate()

        elif rate == "plex":
            self.logger.info(f"Rating {m.title_link} with {m.trakt_rating} on Plex (was {m.plex_rating})", extra={"markup": True})
            if not dry_run:
                m.plex_rate()

    def sync_watched(self, m: Media, dry_run=False):
        if not self.config.sync_watched_status:
            return

        if m.watched_on_plex is m.watched_on_trakt:
            return

        if m.watched_on_plex:
            if not self.config.plex_to_trakt["watched_status"]:
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
            if not self.config.trakt_to_plex["watched_status"]:
                return
            self.logger.info(f"Marking as watched in Plex: {m.title_link}", extra={"markup": True})
            if not dry_run:
                m.mark_watched_plex()

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

    def clear_collected(self, existing_items: Iterable[TraktMedia], keep_ids: set[int], dry_run=False):
        from plextraktsync.trakt.trakt_set import trakt_set

        existing_ids = trakt_set(existing_items)
        delete_ids = existing_ids - keep_ids
        delete_items = (tm for tm in existing_items if tm.trakt in delete_ids)

        n = len(delete_ids)
        for i, tm in enumerate(delete_items, start=1):
            self.logger.info(f"Remove from Trakt collection ({i}/{n}): {tm}")
            if not dry_run:
                self.trakt.remove_from_collection(tm)
