from __future__ import annotations

import datetime
import re
from typing import List, Optional, Union, Dict

from plexapi import X_PLEX_CONTAINER_SIZE
from plexapi.exceptions import BadRequest, NotFound, Unauthorized
from plexapi.library import LibrarySection, MovieSection, ShowSection
from plexapi.media import AudioStream, MediaPart, VideoStream
from plexapi.server import PlexServer, SystemAccount, SystemDevice
from plexapi.video import Episode, Movie, Show
from trakt.utils import timestamp

from plextraktsync.decorators.flatten import flatten_dict, flatten_list
from plextraktsync.decorators.memoize import memoize
from plextraktsync.decorators.nocache import nocache
from plextraktsync.decorators.rate_limit import rate_limit
from plextraktsync.factory import factory
from plextraktsync.logging import logger

AUDIO_CODECS = {
    'lpcm':                 'pcm',
    'mp3':                  None,
    'aac':                  None,
    'ogg':                  'vorbis',
    'wma':                  None,

    'dts':                  '(dca|dta)',
    'dts_ma':               'dtsma',

    'dolby_prologic':       'dolby.?pro',
    'dolby_digital':        'ac.?3',
    'dolby_digital_plus':   'eac.?3',
    'dolby_truehd':         'truehd'
}

# compile patterns in `AUDIO_CODECS`
for k, v in AUDIO_CODECS.items():
    if v is None:
        continue

    try:
        AUDIO_CODECS[k] = re.compile(v, re.IGNORECASE)
    except Exception:
        logger.warn('Unable to compile regex pattern: %r', v, exc_info=True)


class PlexGuid:
    def __init__(self, guid: str, type: str, pm: Optional[PlexLibraryItem] = None):
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
            CONFIG = factory.config()
            x = CONFIG["xbmc-providers"][self.media_type]
        if x == "xbmcnfotv":
            CONFIG = factory.config()
            x = CONFIG["xbmc-providers"]["shows"]

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

        return show

    @property
    @memoize
    def guid_is_imdb_legacy(self):
        guid = self.guid

        # old item, like imdb 'tt0112253'
        return guid[0:2] == "tt" and guid[2:].isnumeric()

    def __str__(self):
        return self.guid


class PlexRatingCollection(dict):
    def __init__(self, plex: PlexApi):
        super(dict, self).__init__()
        self.plex = plex

    def __missing__(self, section_id: int):
        section = self.plex.library_sections[section_id]
        ratings = self.ratings(section)
        self[section_id] = ratings

        return ratings

    @flatten_dict
    def ratings(self, section: PlexLibrarySection):
        ratings = section.find_with_rating()
        for item in ratings:
            yield item.ratingKey, item.userRating


class PlexLibraryItem:
    def __init__(self, item: Union[Movie, Show, Episode], plex: PlexApi = None):
        self.item = item
        self.plex = plex

    @property
    def is_legacy_agent(self):
        return not self.item.guid.startswith('plex://')

    @nocache
    @rate_limit()
    def get_guids(self):
        return self.item.guids

    @property
    @memoize
    def guids(self):
        # return early if legacy agent
        # accessing .guids for legacy agent
        # will make another round-trip to plex server
        # and the result is always empty.
        if self.is_legacy_agent:
            return [PlexGuid(self.item.guid, self.type, self)]

        guids = [PlexGuid(guid.id, self.type, self) for guid in self.get_guids()]

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
    @nocache
    @rate_limit(retries=1)
    def rating(self):
        if self.plex is not None:
            ratings = self.plex.ratings[self.item.librarySectionID]
            user_rating = ratings[self.item.ratingKey] if self.item.ratingKey in ratings else None
        else:
            user_rating = self.item.userRating

        if user_rating is None:
            return None

        return int(user_rating)

    @property
    def seen_date(self):
        return self.date_value(self.item.lastViewedAt)

    @property
    def collected_at(self):
        return self.date_value(self.item.addedAt)

    @property
    def parts(self) -> List[MediaPart]:
        for media in self.item.media:
            yield from media.parts

    @flatten_list
    def streams(self, cls):
        for part in self.parts:
            for stream in part.streams:
                if isinstance(stream, cls):
                    yield stream

    @property
    def audio_streams(self):
        return self.streams(AudioStream)

    @property
    def video_streams(self):
        return self.streams(VideoStream)

    @property
    def audio_channels(self):
        """
        Set to 1.0, 2.0, 2.1, 3.0, 3.1, 4.1, 5.1, 6.1, 7.1, 9.1, or 10.1
        """

        try:
            media = self.item.media[0]
            channels = media.audioChannels
            assert channels is not None
        except (AttributeError, IndexError, TypeError, AssertionError):
            return None

        if channels < 3:
            return '%.01f' % channels

        return '%.01f' % (channels - 0.9)

    @property
    def audio_codec(self):
        try:
            media = self.item.media[0]
            codec = media.audioCodec
            assert codec is not None
        except (AttributeError, IndexError, TypeError, AssertionError):
            return None

        for key, regex in AUDIO_CODECS.items():
            if key == codec:
                return key

            if regex and regex.match(codec):
                return key

        return None

    @property
    def resolution(self):
        """
        Set to uhd_4k, hd_1080p, hd_1080i, hd_720p, sd_480p, sd_480i, sd_576p, or sd_576i.
        """
        try:
            stream = self.video_streams[0]
            title = stream.displayTitle.split(' ')[0]
        except IndexError:
            title = None

        variants = {
            '1080p': 'hd_1080p',
            '720p': 'hd_720p',
        }

        if title in variants:
            return variants[title]

        try:
            media = self.item.media[0]
            width = media.width
            assert width is not None
        except (AttributeError, IndexError, TypeError, AssertionError):
            return None
        # 4k
        if width >= 3840:
            return 'uhd_4k'

        # 1080
        if width >= 1920:
            return 'hd_1080p'

        # 720
        if width >= 1280:
            return 'hd_720p'

        # 576
        if width >= 768:
            return 'sd_576p'

        # 480
        return 'sd_480p'

    @property
    def hdr(self):
        """
        Set to dolby_vision, hdr10, hdr10_plus, or hlg
        """
        try:
            stream = self.video_streams[0]
            colorTrc = stream.colorTrc
        except (AttributeError, IndexError, TypeError):
            return None

        if colorTrc == 'smpte2084':
            return 'hdr10'
        elif colorTrc == 'arib-std-b67':
            return 'hlg'

        try:
            dovi = stream.DOVIPresent
        except AttributeError:
            return None

        if dovi:
            return 'dolby_vision'

        return None

    def watch_progress(self, view_offset):
        percent = view_offset / self.item.duration * 100
        return percent

    def episodes(self):
        for ep in self._get_episodes():
            yield PlexLibraryItem(ep)

    @nocache
    @rate_limit()
    def _get_episodes(self):
        return self.item.episodes()

    @property
    @memoize
    def season_number(self):
        return self.item.seasonNumber

    @property
    @memoize
    def episode_number(self):
        return self.item.index

    @staticmethod
    def date_value(date):
        if not date:
            raise ValueError("Value can't be None")

        return date.astimezone(datetime.timezone.utc)

    def __repr__(self):
        try:
            guid = self.guids[0]
            return f"<{guid.provider}:{guid.id}:{self.item}>"
        except IndexError:
            return f"<{self.item}>"

    def to_json(self):
        metadata = {
            "collected_at": timestamp(self.collected_at),
            "media_type": "digital",
            "resolution": self.resolution,
            "hdr": self.hdr,
            "audio": self.audio_codec,
            "audio_channels": self.audio_channels,
        }

        return {k: v for k, v in metadata.items() if v is not None}


class PlexLibrarySection:
    def __init__(self, section: LibrarySection, plex=None):
        self.section = section
        self.plex = plex

    @nocache
    def __len__(self):
        return self.section.totalSize

    @property
    def type(self):
        return self.section.type

    @property
    def title(self):
        return self.section.title

    @nocache
    def find_by_title(self, name: str):
        try:
            return self.section.get(name)
        except NotFound:
            return None

    def find_with_rating(self):
        filters = {
            'and': [
                {'userRating>>': -1},
            ]
        }

        return self.section.search(filters=filters)

    @nocache
    def find_by_id(self, id: Union[str, int]) -> Optional[Union[Movie, Show, Episode]]:
        try:
            return self.section.fetchItem(int(id))
        except NotFound:
            return None

    def all(self, max_items: int):
        libtype = self.section.TYPE
        key = self.section._buildSearchKey(libtype=libtype, returnKwargs=False)
        start = 0
        size = X_PLEX_CONTAINER_SIZE

        while True:
            items = self.fetch_items(key, size, start)
            if not len(items):
                break

            yield from items

            start += size
            if start > max_items:
                break

    @nocache
    def fetch_items(self, key: str, size: int, start: int):
        return self.section.fetchItems(key, container_start=start, container_size=size)

    def items(self, max_items: int):
        for item in self.all(max_items):
            yield PlexLibraryItem(item, plex=self.plex)

    def __repr__(self):
        return f"<PlexLibrarySection:{self.type}:{self.title}>"


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

    @flatten_list
    def movie_sections(self, library=None) -> List[PlexLibrarySection]:
        for section in self.library_sections.values():
            if section.type != "movie":
                continue
            if library and section.title != library:
                continue
            yield section

    @flatten_list
    def show_sections(self, library=None) -> List[PlexLibrarySection]:
        for section in self.library_sections.values():
            if section.type != "show":
                continue
            if library and section.title != library:
                continue
            yield section

    @memoize
    @nocache
    def fetch_item(self, key: Union[int, str]) -> Optional[PlexLibraryItem]:
        try:
            media = self.plex.library.fetchItem(key)
        except NotFound:
            return None

        return PlexLibraryItem(media)

    def reload_item(self, pm: PlexLibraryItem):
        self.fetch_item.cache_clear()
        return self.fetch_item(pm.item.ratingKey)

    def media_url(self, m: PlexLibraryItem):
        return f"{self.plex_base_url}/details?key={m.item.key}"

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
    @flatten_dict
    @nocache
    def library_sections(self) -> Dict[int, PlexLibrarySection]:
        CONFIG = factory.config()
        for section in self.plex.library.sections():
            if section.title in CONFIG["excluded-libraries"]:
                continue
            yield section.key, PlexLibrarySection(section, plex=self)

    @property
    def library_section_names(self):
        return [s.title for s in self.library_sections.values()]

    @memoize
    @nocache
    def system_device(self, device_id: int) -> SystemDevice:
        return self.plex.systemDevice(device_id)

    @memoize
    @nocache
    def system_account(self, account_id: int) -> SystemAccount:
        return self.plex.systemAccount(account_id)

    @property
    @memoize
    def ratings(self):
        return PlexRatingCollection(self)

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
    def history(self, m, device=False, account=False):
        try:
            history = m.history()
        except Unauthorized as e:
            logger.debug(f"No permission to access play history: {e}")
            return

        for h in history:
            if device:
                h.device = self.system_device(h.deviceID)
            if account:
                h.account = self.system_account(h.accountID)
            yield h

    @nocache
    @rate_limit()
    def mark_watched(self, m):
        m.markWatched()

    @nocache
    def get_sessions(self):
        return self.plex.sessions()
