from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.mixin.SetWindowTitle import SetWindowTitle
from plextraktsync.plex.PlexGuid import PlexGuid
from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem
from plextraktsync.trakt.TraktApi import TraktApi
from plextraktsync.trakt.TraktItem import TraktItem

if TYPE_CHECKING:
    from typing import Any, Generator, Iterable

    from plexapi.video import Episode

    from plextraktsync.media import Media, MediaFactory
    from plextraktsync.plan.WalkConfig import WalkConfig
    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.plex.PlexLibrarySection import PlexLibrarySection


class Walker(SetWindowTitle):
    """
    Class dealing with finding and walking library, movies/shows, episodes
    """

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
            movie = await self.mf.resolve_any(plex)
            if not movie:
                continue
            yield movie

    async def get_plex_shows(self) -> Generator[PlexLibraryItem, Any, None]:
        if self.plan.shows:
            shows = self.media_from_items("show", self.plan.shows)
        elif self.plan.show_sections:
            shows = self.media_from_sections(self.plan.show_sections)
        else:
            return

        async for m in shows:
            yield m

    async def find_episodes(self):
        if self.plan.episodes:
            async for m in self.get_plex_episodes(self.plan.episodes):
                yield m

        async for ps in self.get_plex_shows():
            show = await self.mf.resolve_any(ps)
            if not show:
                continue
            async for m in self.episode_from_show(show):
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

    async def media_from_sections(self, sections: list[PlexLibrarySection]) -> Generator[PlexLibraryItem, Any, None]:
        for section in sections:
            with measure_time(f"{section.title_link} processed", extra={"markup": True}):
                self.set_window_title(f"Processing {section.title}")
                total = len(section)
                it = self.progressbar(
                    section.items(total),
                    total=total,
                    desc=f"Processing {section.title_link}",
                )
                async for m in it:
                    yield m

    async def media_from_items(self, libtype: str, items: list) -> Generator[PlexLibraryItem, Any, None]:
        it = self.progressbar(items, desc=f"Processing {libtype}s")
        async for m in it:
            yield PlexLibraryItem(m, plex=self.plex)

    async def episode_from_show(self, show: Media) -> Generator[Media, Any, None]:
        for pe in show.plex.episodes():
            me = await self.mf.resolve_any(pe, show)
            if not me:
                continue

            me.show = show
            yield me

    async def progressbar(self, iterable: Iterable, **kwargs):
        if self._progressbar:
            pb = self._progressbar(iterable, **kwargs)
            with pb as it:
                async for m in it:
                    yield m
        else:
            async for m in iterable:
                yield m

    async def media_from_traktlist(self, items: Iterable, title="Trakt watchlist") -> Generator[Media, Any, None]:
        it = self.progressbar(items, desc=f"Processing {title}")
        async for media in it:
            tm = TraktItem(media, trakt=self.trakt)
            m = self.mf.resolve_trakt(tm)
            yield m

    async def media_from_plexlist(self, items: Iterable) -> Generator[Media, Any, None]:
        it = self.progressbar(items, desc="Processing Plex watchlist")
        async for media in it:
            pm = PlexLibraryItem(media, plex=self.plex)
            m = await self.mf.resolve_any(pm)
            if not m:
                continue
            yield m
