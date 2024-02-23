from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.factory import logging
from plextraktsync.mixin.SetWindowTitle import SetWindowTitle
from plextraktsync.plex.PlexGuid import PlexGuid
from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem
from plextraktsync.trakt.TraktApi import TraktApi
from plextraktsync.trakt.TraktItem import TraktItem

if TYPE_CHECKING:
    from typing import Any, Generator, Iterable

    from plexapi.video import Episode

    from plextraktsync.media.Media import Media
    from plextraktsync.media.MediaFactory import MediaFactory
    from plextraktsync.plan.WalkConfig import WalkConfig
    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.plex.PlexLibrarySection import PlexLibrarySection


class Walker(SetWindowTitle):
    """
    Class dealing with finding and walking library, movies/shows, episodes
    """
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        plex: PlexApi,
        trakt: TraktApi,
        mf: MediaFactory,
        config: WalkConfig,
        progressbar=None,
    ):
        self._progressbar = progressbar
        self.plex = plex
        self.trakt = trakt
        self.mf = mf
        self.config = config

    @cached_property
    def plan(self):
        from plextraktsync.plan.WalkPlanner import WalkPlanner

        return WalkPlanner(self.plex, self.config).plan()

    @property
    def is_partial(self):
        return self.config.is_partial

    def print_plan(self, print):
        if self.plan.movie_sections:
            print(f"Sync Movie sections: {[x.title_link for x in self.plan.movie_sections]}", extra={"markup": True})

        if self.plan.show_sections:
            print(f"Sync Show sections: {[x.title_link for x in self.plan.show_sections]}", extra={"markup": True})

        if self.plan.movies:
            print(f"Sync Movies: {[x.title for x in self.plan.movies]}")

        if self.plan.shows:
            print(f"Sync Shows: {[x.title for x in self.plan.shows]}")

        if self.plan.episodes:
            print(f"Sync Episodes: {[x.title for x in self.plan.episodes]}")

    def get_plex_movies(self) -> Generator[PlexLibraryItem, Any, None]:
        """
        Iterate over movie sections unless specific movie is requested
        """
        if self.plan.movies:
            movies = self.media_from_items("movie", self.plan.movies)
        elif self.plan.movie_sections:
            movies = self.media_from_sections(self.plan.movie_sections)
        else:
            return

        yield from movies

    def find_movies(self) -> Generator[Media, Any, None]:
        for plex in self.get_plex_movies():
            movie = self.mf.resolve_any(plex)
            if not movie:
                continue
            yield movie

    def get_plex_shows(self) -> Generator[PlexLibraryItem, Any, None]:
        if self.plan.shows:
            shows = self.media_from_items("show", self.plan.shows)
        elif self.plan.show_sections:
            shows = self.media_from_sections(self.plan.show_sections)
        else:
            return

        yield from shows

    def find_episodes(self):
        if self.plan.episodes:
            yield from self.get_plex_episodes(self.plan.episodes)

        # Preload plex shows
        plex_shows = {}

        self.logger.info("Preload shows data")
        for show in self.get_plex_shows():
            plex_shows[show.key] = show
        self.logger.info(f"Preloaded shows data ({len(plex_shows)} shows)")

        show_cache = {}
        for ep in self.episodes_from_sections(self.plan.show_sections):
            show_id = ep.show_id
            ep.show = plex_shows[show_id]
            show = show_cache[show_id] if show_id in show_cache else None
            m = self.mf.resolve_any(ep, show)
            if not m:
                continue
            if show:
                m.show = show
            show_cache[show_id] = m.show
            yield m

    def walk_shows(self, shows: set[Media], title="Processing Shows"):
        if not shows:
            return
        yield from self.progressbar(shows, desc=title)

    def get_plex_episodes(self, episodes: list[Episode]) -> Generator[Media, Any, None]:
        it = self.progressbar(episodes, desc="Processing episodes")
        for pe in it:
            guid = PlexGuid(pe.grandparentGuid, "show")
            show = self.mf.resolve_guid(guid)
            if not show:
                continue
            me = self.mf.resolve_any(PlexLibraryItem(pe, plex=self.plex), show)
            if not me:
                continue

            me.show = show
            yield me

    def media_from_sections(self, sections: list[PlexLibrarySection]) -> Generator[PlexLibraryItem, Any, None]:
        for section in sections:
            with measure_time(f"{section.title_link} processed", extra={"markup": True}):
                self.set_window_title(f"Processing {section.title}")
                it = self.progressbar(
                    section.pager(),
                    desc=f"Processing {section.title_link}",
                )
                yield from it

    def episodes_from_sections(self, sections: list[PlexLibrarySection]) -> Generator[PlexLibraryItem, Any, None]:
        for section in sections:
            with measure_time(f"{section.title_link} processed", extra={"markup": True}):
                self.set_window_title(f"Processing {section.title}")
                it = self.progressbar(
                    section.pager("episode"),
                    desc=f"Processing {section.title_link}",
                )
                yield from it

    def media_from_items(self, libtype: str, items: list) -> Generator[PlexLibraryItem, Any, None]:
        it = self.progressbar(items, desc=f"Processing {libtype}s")
        for m in it:
            yield PlexLibraryItem(m, plex=self.plex)

    def episode_from_show(self, show: Media) -> Generator[Media, Any, None]:
        for pe in show.plex.episodes():
            me = self.mf.resolve_any(pe, show)
            if not me:
                continue

            me.show = show
            yield me

    def progressbar(self, iterable: Iterable, **kwargs):
        if self._progressbar:
            pb = self._progressbar(iterable, **kwargs)
            with pb as it:
                yield from it
        else:
            yield from iterable

    def media_from_traktlist(self, items: Iterable, title="Trakt watchlist") -> Generator[Media, Any, None]:
        it = self.progressbar(items, desc=f"Processing {title}")
        for media in it:
            tm = TraktItem(media)
            m = self.mf.resolve_trakt(tm)
            yield m

    def media_from_plexlist(self, items: Iterable) -> Generator[Media, Any, None]:
        it = self.progressbar(items, desc="Processing Plex watchlist")
        for media in it:
            pm = PlexLibraryItem(media, plex=self.plex)
            m = self.mf.resolve_any(pm)
            if not m:
                continue
            yield m
