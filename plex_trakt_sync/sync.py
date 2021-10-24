from rich.console import Console

from plex_trakt_sync.config import Config
from plex_trakt_sync.decorators.measure_time import measure_time
from plex_trakt_sync.logging import logger
from plex_trakt_sync.media import Media
from plex_trakt_sync.trakt_list_util import TraktListUtil
from plex_trakt_sync.walker import Walker


class Sync:
    def __init__(self, config: Config):
        self.sync_collection_enabled = config["sync"]["collection"]
        self.sync_ratings_enabled = config["sync"]["ratings"]
        self.sync_watched_status_enabled = config["sync"]["watched_status"]

    def sync(self, walker: Walker, dry_run=False):
        listutil = TraktListUtil()
        trakt = walker.trakt
        console = Console()

        with console.status("[bold green]Caching Trakt items..."):
            n = len([
                trakt.watched_movies,
                trakt.watched_shows,
                trakt.movie_collection_set,
                trakt.ratings,
                trakt.watchlist_movies,
                trakt.liked_lists,
            ])
            console.log(f"Cached {n} Trakt items")

        if trakt.watchlist_movies:
            listutil.addList(None, "Trakt Watchlist", trakt_list=trakt.watchlist_movies)

        for lst in trakt.liked_lists:
            listutil.addList(lst['username'], lst['listname'])

        for movie in walker.find_movies():
            self.sync_collection(movie, dry_run=dry_run)
            self.sync_ratings(movie, dry_run=dry_run)
            self.sync_watched(movie, dry_run=dry_run)
            listutil.addPlexItemToLists(movie)

        for episode in walker.find_episodes():
            self.sync_collection(episode, dry_run=dry_run)
            self.sync_watched(episode, dry_run=dry_run)
            listutil.addPlexItemToLists(episode)

        if not dry_run:
            with measure_time("Updated plex watchlist"):
                listutil.updatePlexLists(walker.plex)

        if not dry_run:
            trakt.flush()

    def sync_collection(self, m: Media, dry_run=False):
        if not self.sync_collection_enabled:
            return

        if m.is_collected:
            return

        logger.info(f"To be added to collection: {m}")
        if not dry_run:
            m.add_to_collection()

    def sync_ratings(self, m: Media, dry_run=False):
        if not self.sync_ratings_enabled:
            return

        if m.plex_rating is m.trakt_rating:
            return

        # Plex rating takes precedence over Trakt rating
        if m.plex_rating is not None:
            logger.info(f"Rating {m} with {m.plex_rating} on Trakt")
            if not dry_run:
                m.trakt_rate()
        elif m.trakt_rating is not None:
            logger.info(f"Rating {m} with {m.trakt_rating} on Plex")
            if not dry_run:
                m.plex_rate()

    def sync_watched(self, m: Media, dry_run=False):
        if not self.sync_watched_status_enabled:
            return

        if m.watched_on_plex is m.watched_on_trakt:
            return

        if m.watched_on_plex:
            logger.info(f"Marking as watched in Trakt: {m}")
            if not dry_run:
                m.mark_watched_trakt()
        elif m.watched_on_trakt:
            logger.info(f"Marking as watched in Plex: {m}")
            if not dry_run:
                m.mark_watched_plex()
