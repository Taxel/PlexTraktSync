import datetime
from plexapi.library import MovieSection, ShowSection, LibrarySection
from plexapi.video import Movie, Show
from plex_trakt_sync.decorators import memoize, nocache
from plex_trakt_sync.config import CONFIG


class PlexLibraryItem:
    def __init__(self, item):
        self.item = item

    @property
    @memoize
    def guid(self):
        if self.item.guid.startswith('plex://movie/'):
            if len(self.item.guids) > 0:
                return self.item.guids[0].id
        return self.item.guid

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
        if self.guid_is_imdb_legacy:
            return "imdb"
        x = self.guid.split("://")[0]
        x = x.replace("com.plexapp.agents.", "")
        x = x.replace("themoviedb", "tmdb")
        if x == "xbmcnfo":
            x = CONFIG["xbmc-providers"][self.type]

        return x

    @property
    @memoize
    def id(self):
        if self.guid_is_imdb_legacy:
            return self.item.guid
        x = self.guid.split("://")[1]
        x = x.split("?")[0]
        return x

    @property
    @memoize
    def rating(self):
        return int(self.item.userRating) if self.item.userRating is not None else None

    @property
    @memoize
    def seen_date(self):
        media = self.item
        if not media.lastViewedAt:
            raise ValueError('lastViewedAt is not set')

        date = media.lastViewedAt

        try:
            return date.astimezone(datetime.timezone.utc)
        except ValueError:  # for py<3.6
            return date

    @property
    @memoize
    def guid_is_imdb_legacy(self):
        guid = self.item.guid

        # old item, like imdb 'tt0112253'
        return guid[0:2] == "tt" and guid[2:].isnumeric()

    def __repr__(self):
        return "<%s:%s:%s>" % (self.provider, self.id, self.item)


class PlexLibrarySection:
    def __init__(self, section: LibrarySection):
        self.section = section

    def __len__(self):
        return len(self.all())

    @property
    def title(self):
        return self.section.title

    @memoize
    @nocache
    def all(self):
        return self.section.all()

    @memoize
    def items(self):
        result = []
        for item in (PlexLibraryItem(x) for x in self.all()):
            if item.provider in ["local", "none", "agents.none"]:
                continue
            result.append(item)

        return result


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

    @nocache
    def rate(self, m, rating):
        m.rate(rating)

    @nocache
    def mark_watched(self, m):
        m.markWatched()
