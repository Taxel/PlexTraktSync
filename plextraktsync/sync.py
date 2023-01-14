from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.factory import logger
from plextraktsync.trakt.types import TraktMedia
from plextraktsync.trakt_list_util import TraktListUtil

if TYPE_CHECKING:
    from typing import Iterable, Set

    from plextraktsync.config.Config import Config
    from plextraktsync.media import Media
    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.trakt.TraktApi import TraktApi
    from plextraktsync.walker import Walker


class Sync:
    def __init__(self, config: Config, plex: PlexApi, trakt: TraktApi):
        self.config = config.sync
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
        listutil = TraktListUtil()
        is_partial = walker.is_partial

        if is_partial and self.config.clear_collected:
            logger.warning("Running partial library sync. Clear collected will be disabled.")

        if self.config.update_plex_wl_as_pl:
            if is_partial:
                logger.warning("Running partial library sync. Watchlist as playlist won't update because it needs full library sync.")
            else:
                listutil.addList(None, "Trakt Watchlist", trakt_list=self.trakt.watchlist_movies)

        if self.config.sync_liked_lists:
            if is_partial:
                logger.warning("Partial walk, disabling liked lists updating. Liked lists won't update because it needs full library sync.")
            else:
                for lst in self.trakt.liked_lists:
                    listutil.addList(lst["listid"], lst["listname"])

        if self.config.need_library_walk:
            movie_trakt_ids = set()
            for movie in walker.find_movies():
                self.sync_collection(movie, dry_run=dry_run)
                self.sync_ratings(movie, dry_run=dry_run)
                self.sync_watched(movie, dry_run=dry_run)
                if not is_partial:
                    listutil.addPlexItemToLists(movie)
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
                    listutil.addPlexItemToLists(episode)
                    if self.config.clear_collected:
                        episode_trakt_ids.add(episode.trakt_id)

                if self.config.sync_ratings:
                    # collect shows for later ratings sync
                    shows.add(episode.show)

            if episode_trakt_ids:
                self.clear_collected(self.trakt.episodes_collection, episode_trakt_ids)

            for show in walker.walk_shows(shows, title="Syncing show ratings"):
                self.sync_ratings(show, dry_run=dry_run)

        if self.config.update_plex_wl_as_pl or self.config.sync_liked_lists:
            if is_partial:
                logger.warning("Running partial library sync. Liked lists won't update because it needs full library sync.")
            else:
                with measure_time("Updated liked list"):
                    self.update_playlists(listutil, dry_run=dry_run)

        if walker.config.walk_watchlist and self.sync_wl:
            with measure_time("Updated watchlist"):
                self.sync_watchlist(walker, dry_run=dry_run)

    def update_playlists(self, listutil: TraktListUtil, dry_run=False):
        if dry_run:
            return

        for tl in listutil.lists:
            logger.debug(f"Updating Plex list '{tl.name}' ({len(tl.plex_items)} items)")
            updated = self.plex.update_playlist(tl.name, tl.plex_items_sorted, description=tl.description)
            logger.info(f"Plex list '{tl.name}' ({len(tl.plex_items)} items) {'updated' if updated else 'nothing to update'}")

    def sync_collection(self, m: Media, dry_run=False):
        if not self.config.plex_to_trakt["collection"]:
            return

        if m.is_collected:
            return

        logger.info(f"Adding to collection: '{m.title}'")
        if not dry_run:
            m.add_to_collection()

    def sync_ratings(self, m: Media, dry_run=False):
        if not self.config.sync_ratings:
            return

        if m.plex_rating is m.trakt_rating:
            return

        # Plex rating takes precedence over Trakt rating
        if m.plex_rating is not None:
            if not self.config.plex_to_trakt["ratings"]:
                return
            logger.info(f"Rating '{m.title}' with {m.plex_rating} on Trakt")
            if not dry_run:
                m.trakt_rate()
        elif m.trakt_rating is not None:
            if not self.config.trakt_to_plex["ratings"]:
                return
            logger.info(f"Rating '{m.title}' with {m.trakt_rating} on Plex")
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
                logger.info(f"Show '{show.title}' has been reset in trakt at {m.show_reset_at}.")
                logger.info(f"Marking '{show.title}' as unwatched in Plex.")
                if not dry_run:
                    m.reset_show()
            else:
                logger.info(f"Marking as watched in Trakt: '{m.title}'")
                if not dry_run:
                    m.mark_watched_trakt()
        elif m.watched_on_trakt:
            if not self.config.trakt_to_plex["watched_status"]:
                return
            logger.info(f"Marking as watched in Plex: '{m.title}'")
            if not dry_run:
                m.mark_watched_plex()

    def watchlist_sync_item(self, m: Media, dry_run=False):
        if m.plex is None:
            if self.config.update_plex_wl:
                logger.info(f"Skipping '{m.title}' from Trakt watchlist because not found in Plex Discover")
            elif self.config.update_trakt_wl:
                logger.info(f"Removing '{m.title}' from Trakt watchlist")
                if not dry_run:
                    m.remove_from_trakt_watchlist()
            return

        if m in self.plex_wl:
            if m not in self.trakt_wl:
                if self.config.update_trakt_wl:
                    logger.info(f"Adding '{m.title}' to Trakt watchlist")
                    if not dry_run:
                        m.add_to_trakt_watchlist()
                else:
                    logger.info(f"Removing '{m.title}' from Plex watchlist")
                    if not dry_run:
                        m.remove_from_plex_watchlist()
            else:
                # Plex Online search is inaccurate, and it doesn't offer search by id.
                # Remove known match from trakt watchlist, so that the search would not be attempted.
                # Example, trakt id 187634 where title mismatches:
                #  - "The Vortex": https://trakt.tv/movies/the-vortex-2012
                #  - "Big Bad Bugs": https://app.plex.tv/desktop/#!/provider/tv.plex.provider.vod/details?key=%2Flibrary%2Fmetadata%2F60185c5891c237002b37653d
                del self.trakt_wl[m]
        elif m in self.trakt_wl:
            if self.config.update_plex_wl:
                logger.info(f"Adding '{m.title}' to Plex watchlist")
                if not dry_run:
                    m.add_to_plex_watchlist()
            else:
                logger.info(f"Removing '{m.title}' from Trakt watchlist")
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

    def clear_collected(self, existing_items: Iterable[TraktMedia], keep_ids: Set[int], dry_run=False):
        from plextraktsync.trakt.trakt_set import trakt_set

        existing_ids = trakt_set(existing_items)
        delete_ids = existing_ids - keep_ids
        delete_items = (tm for tm in existing_items if tm.trakt in delete_ids)

        n = len(delete_ids)
        for i, tm in enumerate(delete_items, start=1):
            logger.info(f"Remove from Trakt collection ({i}/{n}): {tm}")
            if not dry_run:
                self.trakt.remove_from_collection(tm)
