from __future__ import annotations

import datetime
from functools import cached_property
from typing import TYPE_CHECKING

from trakt.utils import timestamp

from plextraktsync.decorators.retry import retry
from plextraktsync.factory import factory
from plextraktsync.mixin.RichMarkup import RichMarkup
from plextraktsync.plex.PlexGuid import PlexGuid

if TYPE_CHECKING:
    from plexapi.media import MediaPart

    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.plex.types import PlexMedia


class PlexLibraryItem(RichMarkup):
    def __init__(self, item: PlexMedia, plex: PlexApi = None):
        self.item = item
        self.plex = plex
        self._show = None

    @property
    def key(self):
        return self.item.ratingKey

    @property
    def is_legacy_agent(self):
        return not self.item.guid.startswith("plex://")

    @cached_property
    def is_discover(self):
        # Use __dict__ access to prevent reloads:
        # https://github.com/pkkid/python-plexapi/pull/1093
        return self.item.__dict__["librarySectionID"] is None

    @property
    def web_url(self):
        return self.plex.media_url(self)

    @property
    def discover_url(self):
        if not self.is_discover and not self.is_legacy_agent:
            return self.plex.media_url(self, discover=True)

        return None

    @retry()
    def get_guids(self):
        return self.item.guids

    def __eq__(self, other: PlexLibraryItem):
        """
        Compare with other PlexLibraryItem.
        Items are equal if one of their guids matches
        """
        for guid in self.guids:
            for other_guid in other.guids:
                if guid == other_guid:
                    return True
        return False

    def __hash__(self):
        return hash((guid.provider, guid.id) for guid in self.guids)

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
            "mbid": 1000,
        }
        ordered = sorted(guids, key=lambda guid: sort_order[guid.provider])
        return ordered

    @cached_property
    def duration(self):
        if self.item.duration is None:
            return None

        hours, remainder = divmod(self.item.duration / 1000, 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

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

        if self.is_discover:
            return None

        if self.item.librarySectionID not in self.plex.library_sections:
            return None

        return self.plex.library_sections[self.item.librarySectionID]

    @cached_property
    def edition_title(self):
        if self.type == "movie":
            # Use __dict__ access to prevent reloads
            return self.item.__dict__.get("editionTitle")
        return None

    @cached_property
    def title(self):
        value = self.item.title
        if self.type == "movie" and self.edition_title:
            value = f"{value} ({self.edition_title})"

        if self.type == "episode":
            value = f"{self.item.grandparentTitle}/{self.item.seasonEpisode}/{value}"

        if self.item.year:
            value = f"{value} ({self.item.year})"

        return value

    @retry(retries=1)
    def rating(self, show_id: int = None):
        if not self.is_discover and self.plex is not None:
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
    def is_watched(self):
        return self.item.isPlayed

    @property
    def collected_at(self):
        return self.date_value(self.item.addedAt)

    @property
    def markers(self) -> list[MediaPart]:
        try:
            return self.item.markers
        except AttributeError:
            # If not enough access to server, the markers attribute is missing
            return []

    @property
    def parts(self) -> list[MediaPart]:
        item = self.plex.fetch_item(self.item.ratingKey)
        for media in item.item.media:
            yield from media.parts

    @property
    def audio_streams(self):
        return self.item.audioStreams()

    @property
    def video_streams(self):
        return self.item.videoStreams()

    @property
    def subtitle_streams(self):
        return self.item.subtitleStreams()

    @property
    def audio_channels(self):
        """
        Set to 1.0, 2.0, 2.1, 3.0, 3.1, 4.1, 5.1, 6.1, 7.1, 9.1, or 10.1
        """
        if self.is_discover:
            return None

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
        if self.is_discover:
            return None

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
        if self.is_discover:
            return None
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
        if self.is_discover:
            return None

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

    @retry()
    def _get_episodes(self):
        if self.type == "season":
            show_id = self.item.parentRatingKey
            season = self.item.seasonNumber

            return self.library.search(libtype="episode", filters={"show.id": show_id, "season.index": season})

        return self.library.search(libtype="episode", filters={"show.id": self.item.ratingKey})

    @cached_property
    def season_number(self):
        return self.item.seasonNumber

    @cached_property
    def episode_number(self):
        return self.item.index

    @property
    def show_id(self):
        if self.type != "episode":
            raise RuntimeError("show_id is valid for episodes only")
        return self.item.grandparentRatingKey

    @property
    def show(self):
        if self._show is None:
            self._show = self.plex.fetch_item(self.show_id)

        return self._show

    @show.setter
    def show(self, show):
        if self.type != "episode":
            raise RuntimeError("show_id is valid for episodes only")

        self._show = show

    @staticmethod
    def date_value(date) -> datetime.datetime | None:
        if not date:
            return None

        return date.astimezone(datetime.timezone.utc)

    @property
    def title_link(self):
        if self.plex:
            link = self.plex.media_url(self)

            return self.markup_link(link, self.title)

        return self.markup_title(self.title)

    def __repr__(self):
        try:
            guid = self.guids[0]
        except IndexError:
            return f"<{self.item}>"

        plex = str(self.item).strip("<>")

        # assemble ourselves to handle online sources nan issue
        # https://github.com/pkkid/python-plexapi/issues/1072
        if not isinstance(self.item.ratingKey, int):
            parts = plex.split(":")
            parts[1] = self.item.guid.rsplit("/", 1)[-1]
            plex = ":".join(parts)

        return f"<{guid.provider}:{guid.id}:{plex}>"

    def to_json(self):
        collected_at = None if not self.collected_at else timestamp(self.collected_at)
        metadata = {
            "collected_at": collected_at,
            "media_type": "digital",
            "resolution": self.resolution,
            "hdr": self.hdr,
            "audio": self.audio_codec,
            "audio_channels": self.audio_channels,
        }

        return {k: v for k, v in metadata.items() if v is not None}
