from __future__ import annotations
import datetime
from typing import Union

from plexapi.exceptions import BadRequest, NotFound
from plexapi.library import MovieSection, ShowSection, LibrarySection
from plexapi.server import PlexServer

from plex_trakt_sync.decorators.deprecated import deprecated
from plex_trakt_sync.decorators.memoize import memoize
from plex_trakt_sync.decorators.nocache import nocache
from plex_trakt_sync.config import CONFIG
from trakt.utils import timestamp

from plex_trakt_sync.logging import logger


class PlexGuid:
    def __init__(self, guid: str, type: str, pm: PlexLibraryItem):
        self.guid = guid
        self.type = type
        self.pm = pm

    @property
    @memoize
    def media_type(self):
        return f"{self.type}s"

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
    def guid_is_imdb_legacy(self):
        guid = self.guid

        # old item, like imdb 'tt0112253'
        return guid[0:2] == "tt" and guid[2:].isnumeric()

    def __str__(self):
        return self.guid


class PlexLibraryItem:
    def __init__(self, item):
        self.item = item

    @property
    @memoize
    def guid(self):
        if self.item.guid.startswith('plex://') and len(self.item.guids) > 0:
            return self.guids[0]
        return PlexGuid(self.item.guid, self.type, self)

    @property
    @memoize
    def guids(self):
        guids = [PlexGuid(guid.id, self.type, self) for guid in self.item.guids]
        if not guids:
            guids = [self.guid]

        # take guid in this order:
        # - tmdb, tvdb, then imdb
        # https://github.com/Taxel/PlexTraktSync/issues/313#issuecomment-838447631
        sort_order = {
            "tmdb": 1,
            "tvdb": 2,
            "imdb": 3,
            "local": 100,
        }
        ordered = sorted(guids, key=lambda guid: sort_order[guid.provider])
        return ordered

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
    @deprecated("Use .guid.provider directly")
    def provider(self):
        return self.guid.provider

    @property
    @memoize
    @deprecated("Use .guid.id directly")
    def id(self):
        return self.guid.id

    @property
    @memoize
    @deprecated("Use .guid.is_episode directly")
    def is_episode(self):
        return self.guid.is_episode

    @property
    @memoize
    @deprecated("Use .guid.show_id directly")
    def show_id(self):
        return self.guid.show_id

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

    def date_value(self, date):
        if not date:
            raise ValueError("Value can't be None")

        try:
            return date.astimezone(datetime.timezone.utc)
        except ValueError:  # for py<3.6
            return date

    def __repr__(self):
        return "<%s:%s:%s>" % (self.guid.provider, self.guid.id, self.item)

    def to_json(self):
        return {
            "collected_at": timestamp(self.collected_at),
            "media_type": "digital",
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

    def __init__(self, plex: PlexServer):
        self.plex = plex

    @property
    @memoize
    def plex_base_url(self):
        return f"https://app.plex.tv/desktop/#!/server/{self.plex.machineIdentifier}"

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

    def media_url(self, m: PlexLibraryItem):
        return f"{self.plex_base_url}/details?key={m.item.key}"

    @memoize
    def search(self, title: str, **kwargs):
        result = self.plex.library.search(title, **kwargs)
        for media in result:
            yield PlexLibraryItem(media)

    @property
    @memoize
    @nocache
    def version(self):
        return self.plex.version

    @property
    @memoize
    @nocache
    def updated_at(self):
        return self.plex.updatedAt

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
    def create_playlist(self, name: str, items):
        _, plex_items_sorted = zip(*sorted(dict(reversed(items)).items()))
        self.plex.createPlaylist(name, items=plex_items_sorted)

    @nocache
    def delete_playlist(self, name: str):
        try:
            self.plex.playlist(name).delete()
        except (NotFound, BadRequest):
            logger.debug(f"Playlist '{name}' not found, so it could not be deleted")

    @nocache
    def mark_watched(self, m):
        m.markWatched()
