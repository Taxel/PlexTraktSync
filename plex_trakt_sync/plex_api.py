from plexapi.library import MovieSection, ShowSection
from plex_trakt_sync.decorators import memoize, nocache
from plex_trakt_sync.config import CONFIG


class PlexApi:
    """
    Plex API class abstracting common data access and dealing with requests cache.
    """

    def __init__(self, plex_server):
        self.plex_server = plex_server

    @property
    @memoize
    def movie_sections(self):
        result = []
        for section in self.library_sections:
            if not type(section) is MovieSection:
                continue
            result.append(section)

        return result

    @property
    @memoize
    def show_sections(self):
        result = []
        for section in self.library_sections:
            if not type(section) is ShowSection:
                continue
            result.append(section)

        return result

    @property
    @memoize
    @nocache
    def library_sections(self):
        result = []
        for section in self.plex_server.library.sections():
            if section.title in CONFIG["excluded-libraries"]:
                continue
            result.append(section)

        return result

    @staticmethod
    def is_movie(section):
        return type(section) is MovieSection

    @staticmethod
    def is_show(section):
        return type(section) is ShowSection
