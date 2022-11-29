from __future__ import annotations

import datetime
import re
from typing import Dict, List, Optional, Union

import plexapi
from plexapi import X_PLEX_CONTAINER_SIZE
from plexapi.exceptions import BadRequest, NotFound, Unauthorized
from plexapi.library import LibrarySection
from plexapi.media import AudioStream, MediaPart, SubtitleStream, VideoStream
from plexapi.myplex import MyPlexAccount
from plexapi.playlist import Playlist
from plexapi.server import PlexServer, SystemAccount, SystemDevice
from plexapi.video import Episode, Movie, Show
from trakt.utils import timestamp

from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.decorators.flatten import flatten_dict, flatten_list
from plextraktsync.decorators.memoize import memoize
from plextraktsync.decorators.nocache import nocache
from plextraktsync.decorators.retry import retry
from plextraktsync.factory import factory, logger


class PlexGuid:
    def __init__(self, guid: str, type: str, pm: Optional[PlexLibraryItem] = None):
        self.guid = guid
        self.type = type
        self.pm = pm

    @cached_property
    def media_type(self):
        return f"{self.type}s"

    @cached_property
    def provider(self):
        if self.guid_is_imdb_legacy:
            return "imdb"
        x = self.guid.split("://")[0]
        x = x.replace("com.plexapp.agents.", "")
        x = x.replace("tv.plex.agents.", "")
        x = x.replace("themoviedb", "tmdb")
        x = x.replace("thetvdb", "tvdb")
        if x == "xbmcnfo":
            CONFIG = factory.config
            x = CONFIG["xbmc-providers"][self.media_type]
        if x == "xbmcnfotv":
            CONFIG = factory.config
            x = CONFIG["xbmc-providers"]["shows"]

        return x

    @cached_property
    def id(self):
        if self.guid_is_imdb_legacy:
            return self.guid
        x = self.guid.split("://")[1]
        x = x.split("?")[0]
        return x

    @cached_property
    def is_episode(self):
        """
        Return true of the id is in form of <show>/<season>/<episode>
        """
        parts = self.id.split("/")
        if len(parts) == 3 and all(x.isnumeric() for x in parts):
            return True

        return False

    @cached_property
    def show_id(self):
        if not self.is_episode:
            raise ValueError("show_id is not valid for non-episodes")

        show = self.id.split("/", 1)[0]
        if not show.isnumeric():
            raise ValueError(f"show_id is not numeric: {show}")

        return show

    @cached_property
    def guid_is_imdb_legacy(self):
        guid = self.guid

        # old item, like imdb 'tt0112253'
        return guid[0:2] == "tt" and guid[2:].isnumeric()

    def __str__(self):
        return f"<PlexGuid:{self.guid}>"


class PlexAudioCodec:
    def match(self, codec):
        for key, regex in self.audio_codecs.items():
            if key == codec:
                return key

            if regex and regex.match(codec):
                return key

        return None

    @cached_property
    def audio_codecs(self):
        codecs = {
            "lpcm": "pcm",
            "mp3": None,
            "aac": None,
            "ogg": "vorbis",
            "wma": None,
            "dts": "(dca|dta)",
            "dts_ma": "dtsma",
            "dolby_prologic": "dolby.?pro",
            "dolby_digital": "ac.?3",
            "dolby_digital_plus": "eac.?3",
            "dolby_truehd": "truehd",
        }

        # compile patterns
        for k, v in codecs.items():
            if v is None:
                continue

            try:
                codecs[k] = re.compile(v, re.IGNORECASE)
            except Exception:
                raise RuntimeError(
                    "Unable to compile regex pattern: %r", v, exc_info=True
                )
        return codecs


class PlexLibraryItem:
    def __init__(self, item: Union[Movie, Show, Episode], plex: PlexApi = None):
        self.item = item
        self.plex = plex

    @property
    def is_legacy_agent(self):
        return not self.item.guid.startswith("plex://")

    @nocache
    @retry()
    def get_guids(self):
        return self.item.guids

    @cached_property
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

    @cached_property
    def duration(self):
        hours, remainder = divmod(self.item.duration / 1000, 3600)
        minutes, seconds = divmod(remainder, 60)

        return f'{int(hours):02}:{int(minutes):02}:{int(seconds):02}'

    @cached_property
    def has_media(self):
        return self.type in ["movie", "episode"]

    @cached_property
    def media_type(self):
        return f"{self.type}s"

    @cached_property
    def type(self):
        return self.item.type

    @cached_property
    def title(self):
        value = self.item.title
        if self.type == "movie" and self.item.editionTitle:
            value = f"{value} ({self.item.editionTitle})"

        if self.type == "episode":
            value = f"{self.item.grandparentTitle}/{self.item.seasonEpisode}/{value}"

        value = f"{value} ({self.item.year})"

        return value

    @nocache
    @retry(retries=1)
    def rating(self, show_id: int = None):
        if self.plex is not None:
            return self.plex.ratings.get(self, show_id)
        else:
            user_rating = self.item.userRating

        if user_rating is None:
            return None

        return int(user_rating)

    @property
    def seen_date(self):
        return self.date_value(self.item.lastViewedAt)

    @property
    @nocache
    def is_watched(self):
        return self.item.isPlayed

    @property
    def collected_at(self):
        return self.date_value(self.item.addedAt)

    @property
    def parts(self) -> List[MediaPart]:
        item = self.plex.fetch_item(self.item.ratingKey)
        for media in item.item.media:
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
    def subtitle_streams(self):
        return self.streams(SubtitleStream)

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
            return f"{channels:.01f}"

        return f"{channels - 0.9:.01f}"

    @property
    def audio_codec(self):
        try:
            media = self.item.media[0]
            codec = media.audioCodec
            assert codec is not None
        except (AttributeError, IndexError, TypeError, AssertionError):
            return None

        return factory.plex_audio_codec.match(codec)

    @property
    def resolution(self):
        """
        Set to uhd_4k, hd_1080p, hd_1080i, hd_720p, sd_480p, sd_480i, sd_576p, or sd_576i.
        """
        try:
            stream = self.video_streams[0]
            title = stream.displayTitle.split(" ")[0]
        except (IndexError, AttributeError):
            title = None

        variants = {
            "1080p": "hd_1080p",
            "720p": "hd_720p",
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
            return "uhd_4k"

        # 1080
        if width >= 1920:
            return "hd_1080p"

        # 720
        if width >= 1280:
            return "hd_720p"

        # 576
        if width >= 768:
            return "sd_576p"

        # 480
        return "sd_480p"

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

        if colorTrc == "smpte2084":
            return "hdr10"
        elif colorTrc == "arib-std-b67":
            return "hlg"

        try:
            dovi = stream.DOVIPresent
        except AttributeError:
            return None

        if dovi:
            return "dolby_vision"

        return None

    def watch_progress(self, view_offset):
        percent = view_offset / self.item.duration * 100
        return percent

    def episodes(self):
        for ep in self._get_episodes():
            yield PlexLibraryItem(ep, plex=self.plex)

    @nocache
    @retry()
    def _get_episodes(self):
        return self.item.episodes()

    @cached_property
    def season_number(self):
        return self.item.seasonNumber

    @cached_property
    def episode_number(self):
        return self.item.index

    @staticmethod
    def date_value(date):
        if not date:
            return None

        return date.astimezone(datetime.timezone.utc)

    def __repr__(self):
        try:
            guid = self.guids[0]
            return f"<{guid.provider}:{guid.id}:{str(self.item).strip('<>')}>"
        except IndexError:
            return f"<{self.item}>"

    def to_json(self):
        collected_at = None if not self.collected_at else timestamp(
            self.collected_at)
        metadata = {
            "collected_at": collected_at,
            "media_type": "digital",
            "resolution": self.resolution,
            "hdr": self.hdr,
            "audio": self.audio_codec,
            "audio_channels": self.audio_channels,
        }

        return {k: v for k, v in metadata.items() if v is not None}


class PlexLibrarySection:
    def __init__(self, section: LibrarySection, plex: PlexApi = None):
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

    @nocache
    def search(self, **kwargs):
        return self.section.search(**kwargs)

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
    @retry()
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

    @cached_property
    def account(self):
        return self._plex_account()

    @cached_property
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
    @retry()
    def fetch_item(self, key: Union[int, str]) -> Optional[PlexLibraryItem]:
        try:
            media = self.plex.library.fetchItem(key)
        except NotFound:
            return None

        return PlexLibraryItem(media, plex=self)

    def reload_item(self, pm: PlexLibraryItem):
        try:
            key = pm.item.ratingKey
        except AttributeError as e:
            logger.debug(f"Invalid object: {e}")
            return None

        self.fetch_item.cache_clear()

        return self.fetch_item(key)

    def media_url(self, m: PlexLibraryItem):
        return f"{self.plex_base_url}/details?key={m.item.key}"

    def download(self, m: Union[SubtitleStream], **kwargs):
        url = self.plex.url(m.key)
        token = self.plex._token

        return plexapi.utils.download(url, token, **kwargs)

    def search(self, title: str, **kwargs):
        result = self.plex.library.search(title, **kwargs)
        for media in result:
            yield PlexLibraryItem(media, plex=self)

    @cached_property
    @nocache
    def version(self):
        return self.plex.version

    @cached_property
    @nocache
    def updated_at(self):
        return self.plex.updatedAt

    @cached_property
    @nocache
    @flatten_dict
    def library_sections(self) -> Dict[int, PlexLibrarySection]:
        CONFIG = factory.config
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

    @cached_property
    def ratings(self):
        from plextraktsync.plex.PlexRatings import PlexRatings

        return PlexRatings(self)

    @nocache
    @retry()
    def rate(self, m, rating):
        m.rate(rating)

    @staticmethod
    def same_list(list_a: List[Movie | Show | Episode], list_b: List[Movie | Show | Episode]) -> bool:
        """
        Return true if two list contain same Plex items.
        The comparison is made on ratingKey property,
        the items don't have to actually be identical.
        """

        # Quick way out of lists with different length
        if len(list_a) != len(list_b):
            return False

        a = [m.ratingKey for m in list_a]
        b = [m.ratingKey for m in list_b]

        return a == b

    @nocache
    def update_playlist(self, name: str, items: List[Union[Movie, Show, Episode]], description=None) -> bool:
        """
        Updates playlist (creates if name missing) replacing contents with items[]
        """
        playlist: Optional[Playlist] = None
        try:
            playlist = self.plex.playlist(name)
        except NotFound:
            if len(items) > 0:
                playlist = self.plex.createPlaylist(name, items=items)

        # Skip if playlist could not be made/retrieved
        if playlist is None:
            return False

        updated = False
        if description is not None and description != playlist.summary:
            playlist.edit(summary=description)
            updated = True

        # Skip if nothing to update
        if self.same_list(items, playlist.items()):
            return updated

        playlist.removeItems(playlist.items())
        playlist.addItems(items)
        return True

    @nocache
    @flatten_list
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
    @retry()
    def mark_watched(self, m):
        m.markPlayed()

    @nocache
    @retry()
    def mark_unwatched(self, m):
        m.markUnplayed()

    @nocache
    def has_sessions(self):
        try:
            self.plex.sessions()
            return True
        except Unauthorized:
            return False

    @nocache
    def get_sessions(self):
        return self.plex.sessions()

    @nocache
    def _plex_account(self):
        CONFIG = factory.config
        plex_owner_token = CONFIG.get("PLEX_OWNER_TOKEN")
        plex_account_token = CONFIG.get("PLEX_ACCOUNT_TOKEN")
        plex_username = CONFIG.get("PLEX_USERNAME")
        if plex_owner_token:
            try:
                plex_owner_account = MyPlexAccount(token=plex_owner_token)
                return plex_owner_account.switchHomeUser(plex_username)
            except BadRequest as e:
                logger.error(f"Error during {plex_username} account access: {e}")
        elif plex_account_token:
            try:
                return MyPlexAccount(token=plex_account_token)
            except BadRequest as e:
                logger.error(f"Error during {plex_username} account access: {e}")
        else:
            try:
                return self.plex.myPlexAccount()
            except BadRequest as e:
                logger.error(f"Error during {plex_username} account access: {e}")
        return None

    @nocache
    def watchlist(self) -> Optional[List[Union[Movie, Show]]]:
        if self.account:
            try:
                return self.account.watchlist()
            except BadRequest as e:
                logger.error(f"Error during {self.account.username} watchlist access: {e}")
        return None

    @nocache
    def add_to_watchlist(self, item):
        try:
            self.account.addToWatchlist(item)
        except BadRequest as e:
            logger.error(f"Error when adding {item.title} to Plex watchlist: {e}")

    @nocache
    def remove_from_watchlist(self, item):
        try:
            self.account.removeFromWatchlist(item)
        except BadRequest as e:
            logger.error(f"Error when removing {item.title} from Plex watchlist: {e}")

    @retry()
    def search_online(self, title: str, media_type: str):
        if not self.account:
            return None
        try:
            result = self.account.searchDiscover(title, libtype=media_type)
        except (BadRequest, Unauthorized) as e:
            logger.error(f"{title}: Searching Plex Discover error: {e}")
            return None
        except NotFound:
            return None
        return map(PlexLibraryItem, result)

    @nocache
    def reset_show(self, show, reset_date):
        reset_count = 0
        for ep in show.watched():
            ep_seen_date = PlexLibraryItem(ep).seen_date.replace(tzinfo=None)
            if ep_seen_date < reset_date:
                self.mark_unwatched(ep)
                reset_count += 1
            else:
                logger.debug(f"{show.title} {ep.seasonEpisode} watched at {ep.lastViewedAt} after reset date {reset_date}")
        logger.debug(f"{show.title}: {reset_count} Plex episode(s) marked as unwatched.")
