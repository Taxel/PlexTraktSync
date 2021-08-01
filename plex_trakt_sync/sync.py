from plex_trakt_sync.config import Config
from plex_trakt_sync.logging import logger
from plex_trakt_sync.media import Media
from plex_trakt_sync.trakt_list_util import TraktListUtil
from plex_trakt_sync.walker import Walker


class Sync:
    def __init__(self, config: Config):
        self.sync_collection_enabled = config["sync"]["collection"]
        self.sync_ratings_enabled = config["sync"]["ratings"]
        self.sync_watched_status_enabled = config["sync"]["watched_status"]

    def sync(self, walker: Walker, listutil: TraktListUtil):
        for movie in walker.find_movies():
            self.sync_collection(movie)
            self.sync_ratings(movie)
            self.sync_watched(movie)
            listutil.addPlexItemToLists(movie)

        for episode in walker.find_episodes():
            self.sync_collection(episode)
            self.sync_watched(episode)
            listutil.addPlexItemToLists(episode)

    def sync_collection(self, m: Media):
        if not self.sync_collection_enabled:
            return

        if m.is_collected:
            return

        logger.info(f"To be added to collection: {m}")
        m.add_to_collection()

    def sync_ratings(self, m: Media):
        if not self.sync_ratings_enabled:
            return

        if m.plex_rating is m.trakt_rating:
            return

        # Plex rating takes precedence over Trakt rating
        if m.plex_rating is not None:
            logger.info(f"Rating {m} with {m.plex_rating} on Trakt")
            m.trakt_rate()
        elif m.trakt_rating is not None:
            logger.info(f"Rating {m} with {m.trakt_rating} on Plex")
            m.plex_rate()

    def sync_watched(self, m: Media):
        if not self.sync_watched_status_enabled:
            return

        if m.watched_on_plex is m.watched_on_trakt:
            return

        if m.watched_on_plex:
            logger.info(f"Marking as watched in Trakt: {m}")
            m.mark_watched_trakt()
        elif m.watched_on_trakt:
            logger.info(f"Marking as watched in Plex: {m}")
            m.mark_watched_plex()
