from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from plexapi.media import AudioStream, SubtitleStream, VideoStream
from trakt.utils import timestamp

from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.decorators.flatten import flatten_list
from plextraktsync.decorators.nocache import nocache
from plextraktsync.decorators.retry import retry
from plextraktsync.factory import factory
from plextraktsync.plex.PlexGuid import PlexGuid

if TYPE_CHECKING:
    from typing import List

    from plexapi.media import MediaPart

    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.plex.types import PlexMedia


class PlexLibraryItem:
    def __init__(self, item: PlexMedia, plex: PlexApi = None):
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
    def library(self):
        if not self.plex:
            raise RuntimeError("Need plex property to retrieve library")

        if self.item.librarySectionID not in self.plex.library_sections:
            return None

        return self.plex.library_sections[self.item.librarySectionID]

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
