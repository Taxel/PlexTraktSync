import datetime
from typing import Union

from plexapi.exceptions import NotFound
from plexapi.library import MovieSection, ShowSection, LibrarySection

from plex_trakt_sync.logging import logger
from plex_trakt_sync.decorators import memoize, nocache
from plex_trakt_sync.config import CONFIG
from trakt.utils import timestamp


class PlexLibraryItem:
    def __init__(self, item):
        self.item = item

    @property
    @memoize
    def guid(self):
        if self.item.guid.startswith('plex://'):
            if len(self.item.guids) > 0:
                return self.item.guids[0].id
        return self.item.guid

    @property
    @memoize
    def guids(self):
        return self.item.guids

    @property
    @memoize
    def type(self):
        return f"{self.media_type}s"

    @property
    @memoize
    def media_type(self):
        return self.item.type

    @property
    @memoize
    def provider(self):
        if self.guid_is_imdb_legacy:
            return "imdb"
        x = self.guid.split("://")[0]
        x = x.replace("com.plexapp.agents.", "")
        x = x.replace("tv.plex.agents.", "")
        x = x.replace("themoviedb", "tmdb")
        x = x.replace("thetvdb", "tvdb")
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
        return self.date_value(self.item.lastViewedAt)

    @property
    @memoize
    def collected_at(self):
        return self.date_value(self.item.addedAt)

    def watch_progress(self, view_offset):
        percent = view_offset / self.item.duration * 100
        return percent

    @property
    @memoize
    def guid_is_imdb_legacy(self):
        guid = self.item.guid

        # old item, like imdb 'tt0112253'
        return guid[0:2] == "tt" and guid[2:].isnumeric()

    def date_value(self, date):
        if not date:
            raise ValueError("Value can't be None")

        try:
            return date.astimezone(datetime.timezone.utc)
        except ValueError:  # for py<3.6
            return date

    def __repr__(self):
        return "<%s:%s:%s>" % (self.provider, self.id, self.item)

    def to_json(self):
        return {
            "collected_at": timestamp(self.collected_at),
        }


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

    def items(self):
        for item in (PlexLibraryItem(x) for x in self.all()):
            yield item


class PlexApi:
    """
    Plex API class abstracting common data access and dealing with requests cache.
    """

    def __init__(self, plex):
        self.plex = plex

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
            result.append(PlexLibrarySection(section))

        return result

    @memoize
    def fetch_item(self, key: Union[int, str]):
        media = self.plex.library.fetchItem(key)
        return PlexLibraryItem(media)

    def reload_item(self, pm):
        self.fetch_item.cache_clear()
        return self.fetch_item(pm.item.ratingKey)

    @property
    @memoize
    @nocache
    def library_sections(self):
        result = []
        for section in self.plex.library.sections():
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
