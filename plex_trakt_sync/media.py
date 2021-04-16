from plexapi.exceptions import NotFound
from trakt.errors import TraktException

from plex_trakt_sync.logging import logger
from plex_trakt_sync.plex_api import PlexLibraryItem
from plex_trakt_sync.trakt_api import TraktApi


class Media:
    """
    Class containing Plex and Trakt media items (Movie, Episode)
    """

    def __init__(self, plex, trakt, trakt_api: TraktApi = None):
        self.trakt_api = trakt_api
        self.plex = plex
        self.trakt = trakt
        self.show = None

    @property
    def season_number(self):
        return self.plex.season_number

    @property
    def episode_number(self):
        return self.plex.episode_number

    @property
    def trakt_id(self):
        return self.trakt.trakt

    @property
    def show_trakt_id(self):
        return self.show.trakt_id

    @property
    def is_movie(self):
        return self.plex.type == "movie"

    @property
    def is_collected(self):
        if self.is_movie:
            return self.trakt_id in self.trakt_api.movie_collection_set

        collected = self.trakt_api.collected(self.show.trakt)
        return collected.get_completed(self.season_number, self.episode_number)

    def add_to_collection(self):
        self.trakt_api.add_to_collection(self.trakt, self.plex)

    def __str__(self):
        return str(self.plex)


class MediaFactory:
    """
    Class that is able to resolve Trakt media item from Plex media item and return generic Media class
    """

    def __init__(self, trakt: TraktApi):
        self.trakt = trakt

    def resolve(self, pm: PlexLibraryItem, tm=None):
        try:
            provider = pm.provider
        except NotFound as e:
            logger.error(f"Skipping {pm}: {e}")
            return None

        if provider in ["local", "none", "agents.none"]:
            return None

        if provider not in ["imdb", "tmdb", "tvdb"]:
            logger.error(
                f"{pm}: Unable to parse a valid provider from guid:{pm.guid}, guids:{pm.guids}"
            )
            return None

        try:
            if tm:
                tm = self.trakt.find_episode(tm, pm)
            else:
                tm = self.trakt.find_by_media(pm)
        except TraktException as e:
            logger.warning(f"Skipping {pm}: Trakt errors: {e}")
            return None

        if tm is None:
            logger.warning(f"Skipping {pm}: Not found on Trakt")
            return None

        return Media(pm, tm, trakt_api=self.trakt)
