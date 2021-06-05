import datetime
from typing import Union

from plexapi.library import MovieSection, ShowSection, LibrarySection

from plex_trakt_sync.decorators import memoize, nocache
from plex_trakt_sync.config import CONFIG
from trakt.utils import timestamp


class PlexGuid:
    def __init__(self, guid: str, media_type: str):
        self.guid = guid
        self.media_type = media_type

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
            x = CONFIG["xbmc-providers"][self.media_type]

        return x

    @property
    @memoize
    def id(self):
        if self.guid_is_imdb_legacy:
            return self.guid
        x = self.guid.split("://")[1]
        x = x.split("?")[0]
        return x

    @property
    @memoize
    def guid_is_imdb_legacy(self):
        guid = self.guid

        # old item, like imdb 'tt0112253'
        return guid[0:2] == "tt" and guid[2:].isnumeric()


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
    def media_type(self):
        return f"{self.type}s"

    @property
    @memoize
    def type(self):
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
            x = CONFIG["xbmc-providers"][self.media_type]

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
    def is_episode(self):
        """
        Return true of the id is in form of <show>/<season>/<episode>
        """
        parts = self.id.split("/")
        if len(parts) == 3 and all(x.isnumeric() for x in parts):
            return True

        return False

    @property
    @memoize
    def show_id(self):
        if not self.is_episode:
            raise ValueError("show_id is not valid for non-episodes")

        show = self.id.split("/", 1)[0]
        if not show.isnumeric():
            raise ValueError(f"show_id is not numeric: {show}")

        return int(show)

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

    def episodes(self):
        for ep in self.item.episodes():
            yield PlexLibraryItem(ep)

    @property
    @memoize
    def season_number(self):
        return self.item.seasonNumber

    @property
    @memoize
    def episode_number(self):
        return self.item.index

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

    def movie_sections(self, library=None):
        result = []
        for section in self.library_sections:
            if not type(section) is MovieSection:
                continue
            if library and section.title != library:
                continue
            result.append(PlexLibrarySection(section))

        return result

    def show_sections(self, library=None):
        result = []
        for section in self.library_sections:
            if not type(section) is ShowSection:
                continue
            if library and section.title != library:
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

    @memoize
    def search(self, title: str, **kwargs):
        result = self.plex.library.search(title, **kwargs)
        for media in result:
            yield PlexLibraryItem(media)

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
