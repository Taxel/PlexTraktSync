from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from trakt.sync import PlaybackEntry
from trakt.tv import TVShow

from plextraktsync.mixin.RichMarkup import RichMarkup
from plextraktsync.trakt.TraktLookup import TraktLookup

if TYPE_CHECKING:
    from plextraktsync.media.MediaFactory import MediaFactory
    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem
    from plextraktsync.trakt.TraktApi import TraktApi
    from plextraktsync.trakt.types import TraktMedia


class Media(RichMarkup):
    """
    Class containing Plex and Trakt media items (Movie, Episode)
    """

    trakt: TraktMedia
    plex: PlexLibraryItem

    def __init__(
            self,
            plex: PlexLibraryItem,
            trakt: TraktMedia,
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

    def __eq__(self, other):
        if isinstance(other, PlaybackEntry):
            return self.type == other.type and self.trakt_id == other.trakt

        return False

    def __hash__(self):
        return hash((self.type, self.plex, self.trakt))

    @property
    def title(self):
        if self.plex:
            return self.plex.title

        return f"{self.trakt.title} ({self.trakt.year})"

    @property
    def title_link(self):
        if self.plex:
            return self.plex.title_link

        return self.markup_title(self.title)

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

    @cached_property
    def plex_key(self):
        return self.plex.key

    @property
    def trakt_url(self):
        path = self.trakt.slug if self.trakt.slug else self.trakt_id

        return f"https://trakt.tv/{self.media_type}/{path}"

    @property
    def show(self) -> Media | None:
        if self._show is None and self.mf and not self.plex.is_discover:
            ps = self.plex.show
            if isinstance(self.trakt.show, TVShow):
                ts = self.trakt.show
                ms = self.mf.make_media(trakt=ts, plex=ps)
            else:
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
        self.plex_api.mark_watched(self.plex.item)

    @cached_property
    def trakt_rating(self):
        return self.trakt_api.rating(self.trakt)

    @cached_property
    def plex_rating(self):
        return self.plex.rating()

    def trakt_rate(self):
        rating = self.plex_rating
        if rating is None:
            return
        self.trakt_api.rate(self.trakt, rating.rating, rating.rated_at)

    def plex_rate(self):
        rating = self.trakt_rating
        if rating is None:
            return
        self.plex_api.rate(self.plex.item, rating.rating)

    def plex_history(self, **kwargs):
        if self.plex.is_discover:
            return []
        return self.plex_api.history(self.plex.item, **kwargs)

    def __str__(self):
        if self.plex:
            return str(self.plex)

        return str(self.trakt)
