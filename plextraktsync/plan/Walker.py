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
    from typing import Any, AsyncGenerator, AsyncIterable, Generator, Iterable

    from plexapi.video import Episode

    from plextraktsync.media.Media import Media
    from plextraktsync.media.MediaFactory import MediaFactory
    from plextraktsync.plan.WalkConfig import WalkConfig
    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.plex.PlexLibrarySection import PlexLibrarySection
    from plextraktsync.plex.PlexWatchList import PlexWatchList
    from plextraktsync.trakt.TraktWatchlist import TraktWatchList


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
            print(
                f"Sync Movie sections: {[x.title_link for x in self.plan.movie_sections]}",
                extra={"markup": True},
            )

        if self.plan.show_sections:
            print(
                f"Sync Show sections: {[x.title_link for x in self.plan.show_sections]}",
                extra={"markup": True},
            )

        if self.plan.movies:
            print(f"Sync Movies: {[x.title for x in self.plan.movies]}")

        if self.plan.shows:
            print(f"Sync Shows: {[x.title for x in self.plan.shows]}")

        if self.plan.episodes:
            print(f"Sync Episodes: {[x.title for x in self.plan.episodes]}")

    async def get_plex_movies(self) -> Generator[PlexLibraryItem, Any, None]:
        """
        Iterate over movie sections unless specific movie is requested
        """
        if self.plan.movies:
            movies = self.media_from_items("movie", self.plan.movies)
        elif self.plan.movie_sections:
            movies = self.media_from_sections(self.plan.movie_sections)
        else:
            return

        async for m in movies:
            yield m

    async def find_movies(self) -> Generator[Media, Any, None]:
        async for plex in self.get_plex_movies():
            movie = self.mf.resolve_any(plex)
            if not movie:
                continue
            yield movie

    async def get_plex_shows(self) -> AsyncGenerator[PlexLibraryItem, Any, None]:
        if self.plan.shows:
            it = self.media_from_items("show", self.plan.shows)
        elif self.plan.show_sections:
            it = self.media_from_sections(self.plan.show_sections)
        else:
            return

        async for m in it:
            yield m

    async def find_episodes(self):
        if self.plan.episodes:
            async for m in self.get_plex_episodes(self.plan.episodes):
                yield m

        # Preload plex shows
        plex_shows: dict[int, PlexLibraryItem] = {}
        self.logger.info("Preload shows data")
        async for show in self.get_plex_shows():
            plex_shows[show.key] = show
        self.logger.info(f"Preloaded shows data ({len(plex_shows)} shows)")

        # Preload matches for shows
        show_cache: dict[int, Media] = {}
        self.logger.info("Preload shows matches")
        it = self.progressbar(plex_shows.items(), desc="Processing show matches")
        async for show_id, ps in it:
            show_cache[show_id] = self.mf.resolve_any(ps)
        self.logger.info(f"Preloaded shows matches ({len(show_cache)} shows)")

        async for ep in self.episodes_from_sections(self.plan.show_sections):
            show_id = ep.show_id
            ep.show = plex_shows[show_id]
            show = show_cache.get(show_id)
            m = self.mf.resolve_any(ep, show)
            if not m:
                continue
            if show:
                m.show = show
            show_cache[show_id] = m.show
            yield m

    async def walk_shows(self, shows: set[Media], title="Processing Shows"):
        if not shows:
            return
        async for show in self.progressbar(shows, desc=title):
            yield show

    async def get_plex_episodes(self, episodes: list[Episode]) -> Generator[Media, Any, None]:
        it = self.progressbar(episodes, desc="Processing episodes")
        async for pe in it:
            guid = PlexGuid(pe.grandparentGuid, "show")
            show = self.mf.resolve_guid(guid)
            if not show:
                continue
            me = self.mf.resolve_any(PlexLibraryItem(pe, plex=self.plex), show)
            if not me:
                continue

            me.show = show
            yield me

    async def media_from_sections(self, sections: list[PlexLibrarySection]) -> AsyncGenerator[PlexLibraryItem, Any, None]:
        for section in sections:
            with measure_time(f"{section.title_link} processed", extra={"markup": True}):
                self.set_window_title(f"Processing {section.title}")
                it = self.progressbar(
                    section.pager(),
                    desc=f"Processing {section.title_link}",
                )
                async for m in it:
                    yield m

    async def episodes_from_sections(self, sections: list[PlexLibrarySection]) -> Generator[PlexLibraryItem, Any, None]:
        for section in sections:
            with measure_time(f"{section.title_link} processed", extra={"markup": True}):
                self.set_window_title(f"Processing {section.title}")
                it = self.progressbar(
                    section.pager("episode"),
                    desc=f"Processing {section.title_link}",
                )
                async for m in it:
                    yield m

    async def media_from_items(self, libtype: str, items: list) -> AsyncGenerator[PlexLibraryItem, Any, None]:
        it = self.progressbar(items, desc=f"Processing {libtype}s")
        async for m in it:
            yield PlexLibraryItem(m, plex=self.plex)

    async def episode_from_show(self, show: Media) -> Generator[Media, Any, None]:
        for pe in show.plex.episodes():
            me = self.mf.resolve_any(pe, show)
            if not me:
                continue

            me.show = show
            yield me

    async def progressbar(self, iterable: AsyncIterable | Iterable, **kwargs):
        if self._progressbar:
            pb = self._progressbar(iterable, **kwargs)
            with pb as it:
                async for m in it:
                    yield m
        else:
            for m in iterable:
                yield m

    async def media_from_traktlist(self, items: TraktWatchList, title="Trakt watchlist") -> Generator[Media, Any, None]:
        it = self.progressbar(items, desc=f"Processing {title}")
        async for media in it:
            tm = TraktItem(media)
            m = self.mf.resolve_trakt(tm)
            yield m

    async def media_from_plexlist(self, items: PlexWatchList) -> Generator[Media, Any, None]:
        it = self.progressbar(items, desc="Processing Plex watchlist")
        async for media in it:
            pm = PlexLibraryItem(media, plex=self.plex)
            m = self.mf.resolve_any(pm)
            if not m:
                continue
            yield m
