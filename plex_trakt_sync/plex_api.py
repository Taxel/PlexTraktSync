from plexapi.library import MovieSection, ShowSection, LibrarySection
from plexapi.video import Movie, Show
from plex_trakt_sync.decorators import memoize, nocache
from plex_trakt_sync.config import CONFIG


class PlexLibraryItem:
    def __init__(self, item):
        self.item = item

    @property
    @memoize
    def type(self):
        if type(self.item) is Movie:
            return "movies"
        if type(self.item) is Show:
            return "shows"

    @property
    @memoize
    def provider(self):
        x = self.item.guid.split("://")[0]
        x = x.replace("com.plexapp.agents.", "")
        x = x.replace("themoviedb", "tmdb")
        if x == "xbmcnfo":
            x = CONFIG["xbmc-providers"][self.type]

        return x

    @property
    @memoize
    def id(self):
        x = self.item.guid.split("://")[1]
        x = x.split("?")[0]
        return x

    def __repr__(self):
        return "<%s:%s:%s>" % (self.provider, self.id, self.item)


class PlexLibrarySection:
    def __init__(self, section: LibrarySection):
        self.section = section

    @property
    def title(self):
        return self.section.title

    @memoize
    @nocache
    def all(self):
        return self.section.all()


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
            result.append(PlexLibrarySection(section))

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
