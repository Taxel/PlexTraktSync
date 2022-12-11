from __future__ import annotations

from typing import List, Optional

from plexapi.exceptions import PlexApiException
from requests import RequestException
from trakt.errors import TraktException

from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.factory import logger
from plextraktsync.plex_api import PlexApi, PlexGuid, PlexLibraryItem
from plextraktsync.trakt_api import TraktApi, TraktItem, TraktLookup


class Media:
    """
    Class containing Plex and Trakt media items (Movie, Episode)
    """
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

    @cached_property
    def media_type(self):
        return self.trakt.media_type

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
    def plex_url(self):
        return self.plex_api.media_url(self.plex)

    @property
    def trakt_url(self):
        return f"https://trakt.tv/{self.media_type}/{self.trakt_id}"

    @property
    def show(self) -> Optional[Media]:
        if self._show is None and self.mf:
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

    def add_to_collection(self, batch=False):
        self.trakt_api.add_to_collection(self.trakt, self.plex, batch=batch)

    def remove_from_collection(self):
        self.trakt_api.remove_from_library(self.trakt)

    def add_to_trakt_watchlist(self, batch=False):
        self.trakt_api.add_to_watchlist(self.trakt, batch=batch)

    def add_to_plex_watchlist(self):
        self.plex_api.add_to_watchlist(self.plex.item)

    def remove_from_trakt_watchlist(self, batch=False):
        self.trakt_api.remove_from_watchlist(self.trakt, batch=batch)

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
        self.plex_api.mark_watched(self.plex.item)

    @property
    def trakt_rating(self):
        return self.trakt_api.rating(self.trakt)

    @cached_property
    def plex_rating(self):
        show_id = self.show.plex.item.ratingKey if self.media_type == "episodes" else None
        return self.plex.rating(show_id)

    def trakt_rate(self):
        self.trakt_api.rate(self.trakt, self.plex_rating)

    def plex_rate(self):
        self.plex_api.rate(self.plex.item, self.trakt_rating)

    def plex_history(self, **kwargs):
        return self.plex_api.history(self.plex.item, **kwargs)

    def __str__(self):
        return str(self.plex)


class MediaFactory:
    """
    Class that is able to resolve Trakt media item from Plex media item and vice versa and return generic Media class
    """

    def __init__(self, plex: PlexApi, trakt: TraktApi):
        self.plex = plex
        self.trakt = trakt

    def resolve_any(self, pm: PlexLibraryItem, show: Media = None) -> Optional[Media]:
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
            logger.warning(f"{guid.pm.item}: Skipping {guid} because provider {guid.provider} has no external Id")

            return None

        if guid.provider not in ["imdb", "tmdb", "tvdb"]:
            logger.error(
                f"{guid.pm.item}: Unable to parse a valid provider from guid {guid}"
            )
            return None

        try:
            if show:
                tm = self.trakt.find_episode_guid(guid, show.seasons)
            else:
                tm = self.trakt.find_by_guid(guid)
        except (TraktException, RequestException) as e:
            logger.warning(f"{guid.pm.item}: Skipping guid {guid} Trakt errors: {e}")
            return None

        if tm is None:
            logger.warning(f"{guid.pm.item}: Skipping guid {guid} not found on Trakt")
            return None

        return self.make_media(guid.pm, tm)

    def resolve_trakt(self, tm: TraktItem) -> Media:
        """Find Plex media from Trakt id using Plex Search and Discover"""
        result = self.plex.search_online(tm.item.title, tm.type)
        pm = self._guid_match(result, tm)
        return self.make_media(pm, tm.item)

    def make_media(self, plex: PlexLibraryItem, trakt):
        return Media(plex, trakt, plex_api=self.plex, trakt_api=self.trakt, mf=self)

    def _guid_match(self, candidates: List[PlexLibraryItem], tm: TraktItem) -> Optional[PlexLibraryItem]:
        if candidates:
            for pm in candidates:
                for guid in pm.guids:
                    for provider in ["tmdb", "imdb", "tvdb"]:
                        if guid.provider == provider and hasattr(tm.item, provider) and guid.id == str(getattr(tm.item, provider)):
                            return pm
        return None
