from typing import Dict, Union

from plexapi.video import Movie, Show
from trakt.movies import Movie as TraktMovie
from trakt.tv import TVShow

from plextraktsync.config import Config
from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.decorators.flatten import flatten_dict
from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.factory import logger
from plextraktsync.media import Media
from plextraktsync.plex_api import PlexApi
from plextraktsync.trakt_api import TraktApi
from plextraktsync.trakt_list_util import TraktListUtil
from plextraktsync.walker import Walker


class SyncConfig:
    def __init__(self, config: Config):
        self.config = dict(config["sync"])

    def __getitem__(self, key):
        return self.config[key]

    def __contains__(self, key):
        return key in self.config

    def get(self, section, key):
        return self[key] if key in self else self[section][key]

    @cached_property
    def trakt_to_plex(self):
        return {
            "watched_status": self.get("trakt_to_plex", "watched_status"),
            "ratings": self.get("trakt_to_plex", "ratings"),
            "liked_lists": self.get("trakt_to_plex", "liked_lists"),
            "watchlist": self.get("trakt_to_plex", "watchlist"),
            "watchlist_as_playlist": self.get("trakt_to_plex", "watchlist_as_playlist"),
        }

    @cached_property
    def plex_to_trakt(self):
        return {
            "watched_status": self.get("plex_to_trakt", "watched_status"),
            "ratings": self.get("plex_to_trakt", "ratings"),
            "collection": self.get("plex_to_trakt", "collection"),
            "watchlist": self.get("plex_to_trakt", "watchlist"),
        }

    @cached_property
    def sync_ratings(self):
        return self.trakt_to_plex["ratings"] or self.plex_to_trakt["ratings"]

    @cached_property
    def sync_watchlists(self):
        return self.trakt_to_plex["watchlist"] or self.plex_to_trakt["watchlist"]

    @cached_property
    def sync_watched_status(self):
        return (
            self.trakt_to_plex["watched_status"] or self.plex_to_trakt["watched_status"]
        )

    @cached_property
    def update_plex_wl(self):
        return self.trakt_to_plex["watchlist"] and not self.trakt_to_plex["watchlist_as_playlist"]

    @cached_property
    def update_plex_wl_as_pl(self):
        return self.trakt_to_plex["watchlist"] and self.trakt_to_plex["watchlist_as_playlist"]

    @cached_property
    def update_trakt_wl(self):
        return self.plex_to_trakt["watchlist"]

    @cached_property
    def sync_wl(self):
        return self.update_plex_wl or self.update_trakt_wl

    @cached_property
    def sync_liked_lists(self):
        return self.trakt_to_plex["liked_lists"]

    @cached_property
    def need_library_walk(self):
        return any([
            self.update_plex_wl_as_pl,
            self.sync_watched_status,
            self.sync_ratings,
            self.plex_to_trakt["collection"],
            self.sync_liked_lists,
        ])


class Sync:
    def __init__(self, config: Config, plex: PlexApi, trakt: TraktApi):
        self.config = config.sync
        self.plex = plex
        self.trakt = trakt

    @cached_property
    @flatten_dict
    def plex_wl(self) -> Dict[str, Union[Movie, Show]]:
        """
        Return map of [Guid, Plex] of Plex Watchlist
        """
        for pm in self.plex.watchlist():
            yield pm.guid, pm

    @cached_property
    def sync_wl(self):
        return self.config.sync_wl and len(self.plex_wl) > 0

    @cached_property
    @flatten_dict
    def trakt_wl_movies(self) -> Dict[int, TraktMovie]:
        for tm in self.trakt.watchlist_movies:
            yield tm.trakt, tm

    @cached_property
    @flatten_dict
    def trakt_wl_shows(self) -> Dict[int, TVShow]:
        for tm in self.trakt.watchlist_shows:
            yield tm.trakt, tm

    def sync(self, walker: Walker, dry_run=False):
        listutil = TraktListUtil()
        is_partial = walker.is_partial

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
            for movie in walker.find_movies():
                self.sync_collection(movie, dry_run=dry_run)
                self.sync_ratings(movie, dry_run=dry_run)
                self.sync_watched(movie, dry_run=dry_run)
                if not is_partial:
                    listutil.addPlexItemToLists(movie)

            shows = set()
            for episode in walker.find_episodes():
                self.sync_collection(episode, dry_run=dry_run)
                self.sync_ratings(episode, dry_run=dry_run)
                self.sync_watched(episode, dry_run=dry_run)
                if not is_partial:
                    listutil.addPlexItemToLists(episode)
                if self.config.sync_ratings:
                    # collect shows for later ratings sync
                    shows.add(episode.show)

            for show in walker.walk_shows(shows, title="Syncing show ratings"):
                self.sync_ratings(show, dry_run=dry_run)

        if self.sync_wl or self.config.sync_liked_lists:
            if is_partial:
                logger.warning("Partial walk, watchlist and/or liked list updating was skipped")
            else:
                with measure_time("Updated watchlist and/or liked list"):
                    if self.config.update_plex_wl_as_pl or self.config.sync_liked_lists:
                        self.update_playlists(listutil, dry_run=dry_run)
                    if self.sync_wl:
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

        logger.info(f"Adding to collection: {m}")
        if not dry_run:
            m.add_to_collection(batch=True)

    def sync_ratings(self, m: Media, dry_run=False):
        if not self.config.sync_ratings:
            return

        if m.plex_rating is m.trakt_rating:
            return

        # Plex rating takes precedence over Trakt rating
        if m.plex_rating is not None:
            if not self.config.plex_to_trakt["ratings"]:
                return
            logger.info(f"Rating {m} with {m.plex_rating} on Trakt")
            if not dry_run:
                m.trakt_rate()
        elif m.trakt_rating is not None:
            if not self.config.trakt_to_plex["ratings"]:
                return
            logger.info(f"Rating {m} with {m.trakt_rating} on Plex")
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
                logger.info(f"Marking as watched in Trakt: {m}")
                if not dry_run:
                    m.mark_watched_trakt()
        elif m.watched_on_trakt:
            if not self.config.trakt_to_plex["watched_status"]:
                return
            logger.info(f"Marking as watched in Plex: {m}")
            if not dry_run:
                m.mark_watched_plex()

    def watchlist_sync_item(self, m: Media, dry_run=False):
        if self.sync_wl:
            if m.media_type == "movies":
                trakt_wl = self.trakt_wl_movies
            else:
                trakt_wl = self.trakt_wl_shows
            if m.plex is None:
                if self.config.update_plex_wl:
                    logger.info(f"Skipping '{m.trakt.title}' from Trakt watchlist because not found in Plex Discover")
                elif self.config.update_trakt_wl:
                    logger.info(f"Removing '{m.trakt.title}' from Trakt watchlist")
                    if not dry_run:
                        m.remove_from_trakt_watchlist(batch=True)
            elif m.plex.item.guid in self.plex_wl:
                if m.trakt.trakt not in trakt_wl:
                    if self.config.update_trakt_wl:
                        logger.info(f"Adding '{m.plex.item.title}' to Trakt watchlist")
                        if not dry_run:
                            m.add_to_trakt_watchlist(batch=True)
                    else:
                        logger.info(f"Removing '{m.trakt.title}' from Plex watchlist")
                        if not dry_run:
                            m.remove_from_plex_watchlist()
                else:
                    trakt_wl.pop(m.trakt.trakt)
            else:
                if m.trakt.trakt in trakt_wl:
                    if self.config.update_plex_wl:
                        logger.info(f"Adding '{m.trakt.title}' to Plex watchlist")
                        if not dry_run:
                            m.add_to_plex_watchlist()
                    else:
                        logger.info(f"Removing '{m.trakt.title}' from Trakt watchlist")
                        if not dry_run:
                            m.remove_from_trakt_watchlist(batch=True)

    def sync_watchlist(self, walker: Walker, dry_run=False):
        for m in walker.media_from_plexlist(list(self.plex_wl.values())):
            self.watchlist_sync_item(m, dry_run)
        for m in walker.media_from_traktlist(list(self.trakt_wl_movies.values()) + list(self.trakt_wl_shows.values())):
            self.watchlist_sync_item(m, dry_run)
