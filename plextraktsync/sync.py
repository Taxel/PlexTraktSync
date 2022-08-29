from plextraktsync.config import Config
from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.logging import logger
from plextraktsync.media import Media
from plextraktsync.trakt_list_util import TraktListUtil
from plextraktsync.walker import Walker


class SyncConfig:
    def __init__(self, config: Config):
        self.config = dict(config["sync"])

    def __getitem__(self, key):
        return self.config[key]

    def __contains__(self, key):
        return key in self.config

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
    def sync_watched_status(self):
        return (
            self.trakt_to_plex["watched_status"] or self.plex_to_trakt["watched_status"]
        )

    def get(self, section, key):
        return self[key] if key in self else self[section][key]


class Sync:
    def __init__(self, config: Config):
        self.config = SyncConfig(config)

    def sync(self, walker: Walker, dry_run=False):
        listutil = TraktListUtil()
        trakt = walker.trakt
        plex = walker.plex
        self.update_plex_wl = self.config.trakt_to_plex["watchlist"] and not self.config.trakt_to_plex["watchlist_as_playlist"]
        self.update_plex_wl_as_pl = self.config.trakt_to_plex["watchlist"] and self.config.trakt_to_plex["watchlist_as_playlist"]
        self.update_trakt_wl = self.config.plex_to_trakt["watchlist"]
        self.sync_wl = self.config.trakt_to_plex["watchlist"] or self.config.plex_to_trakt["watchlist"]
        if self.sync_wl:
            self.trakt_wl_movies = {tm.trakt: tm for tm in trakt.watchlist_movies} or {}
            self.trakt_wl_shows = {tm.trakt: tm for tm in trakt.watchlist_shows} or {}
            self.plex_wl = {pm.guid: pm for pm in plex.watchlist()} or {}

        if self.update_plex_wl_as_pl:
            listutil.addList(None, "Trakt Watchlist", trakt_list=trakt.watchlist_movies)

        if self.config.trakt_to_plex["liked_lists"]:
            for lst in trakt.liked_lists:
                listutil.addList(lst["username"], lst["listname"])

        for movie in walker.find_movies():
            self.sync_collection(movie, dry_run=dry_run)
            self.sync_ratings(movie, dry_run=dry_run)
            self.sync_watched(movie, dry_run=dry_run)
            listutil.addPlexItemToLists(movie)
        trakt.flush()

        shows = set()
        for episode in walker.find_episodes():
            self.sync_collection(episode, dry_run=dry_run)
            self.sync_ratings(episode, dry_run=dry_run)
            self.sync_watched(episode, dry_run=dry_run)
            listutil.addPlexItemToLists(episode)
            if self.config.sync_ratings:
                # collect shows for later ratings sync
                shows.add(episode.show)
        trakt.flush()

        for show in walker.walk_shows(shows, title="Syncing show ratings"):
            self.sync_ratings(show, dry_run=dry_run)

        if self.sync_wl:
            with measure_time("Updated watchlist"):
                if self.update_plex_wl_as_pl:
                    if not dry_run:
                        listutil.updatePlexLists(walker.plex)
                else:
                    self.sync_watchlist(walker, dry_run=dry_run)

        if not dry_run:
            trakt.flush()

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
            if m.is_movie:
                trakt_wl = self.trakt_wl_movies
            else:
                trakt_wl = self.trakt_wl_shows
            if m.plex.item.guid in self.plex_wl:
                if m.trakt.trakt not in trakt_wl:
                    if self.update_trakt_wl:
                        logger.info(f"Adding {m.plex.item.title} to Trakt watchlist")
                        if not dry_run:
                            m.add_to_trakt_watchlist(batch=True)
                    else:
                        logger.info(f"Removing {m.trakt.title} from Plex watchlist")
                        if not dry_run:
                            m.remove_from_plex_watchlist()
                else:
                    trakt_wl.pop(m.trakt.trakt)
            else:
                if m.trakt.trakt in trakt_wl:
                    if self.update_plex_wl:
                        logger.info(f"Adding {m.trakt.title} to Plex watchlist")
                        if not dry_run:
                            m.add_to_plex_watchlist()
                    else:
                        logger.info(f"Removing {m.trakt.title} from Trakt watchlist")
                        if not dry_run:
                            m.remove_from_trakt_watchlist(batch=True)

    def sync_watchlist(self, walker: Walker, dry_run=False):
        """After plex library processing, sync watchlist items not in the plex library"""
        for m in walker.media_from_plexlist(list(self.plex_wl.values())):
            self.watchlist_sync_item(m, dry_run)
        for m in walker.media_from_traktlist(list(self.trakt_wl_movies.values()) + list(self.trakt_wl_shows.values())):
            self.watchlist_sync_item(m, dry_run)
