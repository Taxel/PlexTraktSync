from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plexapi.exceptions import PlexApiException
from requests import RequestException
from trakt.errors import TraktException

from plextraktsync.factory import logger
from plextraktsync.trakt.TraktLookup import TraktLookup
from rich.markup import escape

if TYPE_CHECKING:
    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.plex.PlexGuid import PlexGuid
    from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem
    from plextraktsync.trakt.TraktApi import TraktApi
    from plextraktsync.trakt.TraktItem import TraktItem
    from plextraktsync.trakt.types import TraktMedia


class Media:
    """
    Class containing Plex and Trakt media items (Movie, Episode)
    """
    trakt: TraktMedia
    plex: PlexLibraryItem

    def __init__(
            self,
            plex: PlexLibraryItem,
            trakt,
            plex_api: PlexApi = None,
            trakt_api: TraktApi = None,
            mf: MediaFactory = None,
    ):
        self.plex_api = plex_api
        self.trakt_api = trakt_api
        self.mf = mf
        self.plex = plex
        self.trakt = trakt
        self._show = None

    @property
    def title(self):
        if self.plex:
            return self.plex.title

        return f"{self.trakt.title} ({self.trakt.year})"

    @property
    def title_link(self):
        if self.plex:
            link = self.plex_api.media_url(self.plex)

            return f"[link={link}][green]{escape(self.title)}[/][/]"

        return f"[green]{escape(self.title)}[/]"

    @cached_property
    def media_type(self):
        return self.trakt.media_type

    @cached_property
    def type(self):
        """
        Return "movie", "show", "season", "episode"
        """
        # NB: TVSeason does not have "media_type" property
        return self.trakt.media_type[:-1]

    @property
    def season_number(self):
        return self.trakt.season

    @property
    def episode_number(self):
        return self.trakt.number

    @cached_property
    def trakt_id(self):
        return self.trakt.trakt

    @property
    def trakt_url(self):
        return f"https://trakt.tv/{self.media_type}/{self.trakt_id}"

    @property
    def show(self) -> Media | None:
        if self._show is None and self.mf and not self.plex.is_discover:
            # TODO: fetch show for discover items
            ps = self.plex_api.fetch_item(self.plex.item.grandparentRatingKey)
            ms = self.mf.resolve_any(ps)
            self._show = ms

        return self._show

    @show.setter
    def show(self, show):
        self._show = show

    @property
    def show_trakt_id(self):
        show_id = getattr(self.trakt, "show_id", None)
        if show_id:
            return show_id
        return self.show.trakt_id

    @cached_property
    def show_reset_at(self):
        watched = self.trakt_api.watched_shows
        return watched.reset_at(self.show_trakt_id)

    @cached_property
    def is_movie(self):
        return self.plex.type == "movie"

    @cached_property
    def is_episode(self):
        return self.plex.type == "episode"

    @property
    def is_collected(self):
        if self.is_movie:
            return self.trakt_id in self.trakt_api.movie_collection_set
        elif not self.is_episode:
            raise RuntimeError(
                f"is_collected: Unsupported media type: {self.media_type}"
            )

        collected = self.trakt_api.collected_shows
        return collected.is_collected(
            self.show_trakt_id, self.season_number, self.episode_number)

    def add_to_collection(self):
        self.trakt_api.add_to_collection(self.trakt, self.plex)

    def remove_from_collection(self):
        self.trakt_api.remove_from_collection(self.trakt)

    def add_to_trakt_watchlist(self):
        self.trakt_api.add_to_watchlist(self.trakt)

    def add_to_plex_watchlist(self):
        self.plex_api.add_to_watchlist(self.plex.item)

    def remove_from_trakt_watchlist(self):
        self.trakt_api.remove_from_watchlist(self.trakt)

    def remove_from_plex_watchlist(self):
        self.plex_api.remove_from_watchlist(self.plex.item)

    @cached_property
    def seasons(self):
        if self.media_type != "shows":
            raise RuntimeError(f"seasons: Unsupported media type: {self.media_type}")

        return TraktLookup(self.trakt)

    @property
    def watched_on_plex(self):
        return self.plex.is_watched

    @property
    def watched_on_trakt(self):
        if self.is_movie:
            return self.trakt_id in self.trakt_api.watched_movies
        elif not self.is_episode:
            raise RuntimeError(
                f"watched_on_trakt: Unsupported media type: {self.media_type}"
            )

        watched = self.trakt_api.watched_shows
        return watched.get_completed(
            self.show_trakt_id, self.season_number, self.episode_number
        )

    @property
    def watched_before_reset(self):
        """
        Return True if episode was watched before show reset (if there is a reset).
        """
        if not self.is_episode:
            raise RuntimeError("watched_before_reset is valid for episodes only")

        return self.show_reset_at and self.plex.seen_date.replace(tzinfo=None) < self.show_reset_at

    def reset_show(self):
        """
        Mark unwatched all Plex episodes played before the show reset date.
        """
        self.plex_api.reset_show(show=self.plex.item.show(), reset_date=self.show_reset_at)

    def mark_watched_trakt(self):
        if self.is_movie:
            self.trakt_api.mark_watched(self.trakt, self.plex.seen_date)
        elif self.is_episode:
            self.trakt_api.mark_watched(self.trakt, self.plex.seen_date, self.show_trakt_id)
        else:
            raise RuntimeError(
                f"mark_watched_trakt: Unsupported media type: {self.media_type}"
            )

    def mark_watched_plex(self):
        self.plex_api.mark_watched(self.plex.item, self.plex.is_discover)

    @property
    def trakt_rating(self):
        return self.trakt_api.rating(self.trakt)

    @cached_property
    def plex_rating(self):
        show_id = self.show.plex.item.ratingKey if self.media_type == "episodes" and not self.plex.is_discover else None
        return self.plex.rating(show_id)

    def trakt_rate(self):
        self.trakt_api.rate(self.trakt, self.plex_rating)

    def plex_rate(self):
        self.plex_api.rate(self.plex.item, self.trakt_rating)

    def plex_history(self, **kwargs):
        if self.plex.is_discover:
            return []
        return self.plex_api.history(self.plex.item, **kwargs)

    def __str__(self):
        if self.plex:
            return str(self.plex)

        return str(self.trakt)


class MediaFactory:
    """
    Class that is able to resolve Trakt media item from Plex media item and vice versa and return generic Media class
    """

    def __init__(self, plex: PlexApi, trakt: TraktApi):
        self.plex = plex
        self.trakt = trakt

    def resolve_any(self, pm: PlexLibraryItem, show: Media = None) -> Media | None:
        try:
            guids = pm.guids
        except (PlexApiException, RequestException) as e:
            logger.error(f"Skipping {pm}: {e}")
            return None

        for guid in guids:
            m = self.resolve_guid(guid, show)
            if m:
                return m

        return None

    def resolve_guid(self, guid: PlexGuid, show: Media = None):
        if guid.provider in ["local", "none", "agents.none"]:
            logger.warning(f"Skipping {guid} because provider {guid.provider} has no external Id")

            return None

        if guid.provider not in ["imdb", "tmdb", "tvdb"]:
            logger.error(f"Unable to parse a valid provider from {guid}")
            return None

        try:
            if show:
                tm = self.trakt.find_episode_guid(guid, show.seasons)
            else:
                tm = self.trakt.find_by_guid(guid)
        except (TraktException, RequestException) as e:
            logger.warning(f"Skipping {guid}: Trakt errors: {e}")
            return None

        if tm is None:
            logger.warning(f"Skipping {guid}: not found on Trakt")
            return None

        return self.make_media(guid.pm, tm)

    def resolve_trakt(self, tm: TraktItem) -> Media:
        """Find Plex media from Trakt id using Plex Search and Discover"""
        result = self.plex.search_online(tm.item.title, tm.type)
        pm = self._guid_match(result, tm)
        return self.make_media(pm, tm.item)

    def make_media(self, plex: PlexLibraryItem, trakt):
        return Media(plex, trakt, plex_api=self.plex, trakt_api=self.trakt, mf=self)

    def _guid_match(self, candidates: list[PlexLibraryItem], tm: TraktItem) -> PlexLibraryItem | None:
        if candidates:
            for pm in candidates:
                for guid in pm.guids:
                    for provider in ["tmdb", "imdb", "tvdb"]:
                        if guid.provider == provider and hasattr(tm.item, provider) and guid.id == str(getattr(tm.item, provider)):
                            return pm
        return None
