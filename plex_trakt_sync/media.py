from plexapi.exceptions import NotFound

from plex_trakt_sync.logging import logger
from plex_trakt_sync.plex_api import PlexLibraryItem
from plex_trakt_sync.trakt_api import TraktApi


class Media:
    """
    Class containing Plex and Trakt media items (Movie, Episode)
    """

    def __init__(self, pm, tm):
        self.pm = pm
        self.tm = tm
        self.show = None

    @property
    def plex(self):
        return self.pm

    @property
    def trakt(self):
        return self.tm


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

        if tm:
            tm = self.trakt.find_episode(tm, pm)
        else:
            tm = self.trakt.find_by_media(pm)
        if tm is None:
            logger.warning(f"Skipping {pm}: Not found on Trakt")
            return None

        return Media(pm, tm)
