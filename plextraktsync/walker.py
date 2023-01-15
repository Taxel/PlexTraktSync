from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, NamedTuple

from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.plex.PlexGuid import PlexGuid
from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem
from plextraktsync.trakt.TraktApi import TraktApi
from plextraktsync.trakt.TraktItem import TraktItem

if TYPE_CHECKING:
    from typing import Any, Generator, Iterable, List, Set

    from plexapi.video import Episode, Movie, Show

    from plextraktsync.media import Media, MediaFactory
    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.plex.PlexLibrarySection import PlexLibrarySection


class WalkConfig:
    walk_movies = True
    walk_shows = True
    walk_watchlist = True
    library = []
    show = []
    movie = []
    id = []

    def __init__(self, movies=True, shows=True, watchlist=True):
        self.walk_movies = movies
        self.walk_shows = shows
        self.walk_watchlist = watchlist

    def update(self, movies=None, shows=None, watchlist=None):
        if movies is not None:
            self.walk_movies = movies
        if shows is not None:
            self.walk_shows = shows
        if watchlist is not None:
            self.walk_watchlist = watchlist

        return self

    def add_library(self, library):
        self.library.append(library)

    def add_id(self, id):
        self.id.append(id)

    def add_show(self, show):
        self.show.append(show)

    def add_movie(self, movie):
        self.movie.append(movie)

    @property
    def is_partial(self):
        """
        Returns true if partial library walk is performed.
        Due the way watchlist is filled, watchlists should only be updated on full walk.
        """
        # Single item provided
        if self.library or self.movie or self.show or self.id:
            return True

        # Must sync both movies and shows to be full sync
        return not self.walk_movies or not self.walk_shows

    def is_valid(self):
        # Single item provided
        if self.library or self.movie or self.show or self.id:
            return True

        # Full sync of movies or shows
        if self.walk_movies or self.walk_shows:
            return True

        if self.walk_watchlist:
            return True

        return False


class WalkPlan(NamedTuple):
    movie_sections: List[PlexLibrarySection]
    show_sections: List[PlexLibrarySection]
    movies: List[Movie]
    shows: List[Show]
    episodes: List[Episode]


class WalkPlanner:
    def __init__(self, plex: PlexApi, config: WalkConfig):
        self.plex = plex
        self.config = config

    def plan(self):
        movie_sections, show_sections = self.find_sections()
        movies, shows, episodes = self.find_by_id(movie_sections, show_sections)
        shows = self.find_from_sections_by_title(show_sections, self.config.show, shows)
        movies = self.find_from_sections_by_title(
            movie_sections, self.config.movie, movies
        )

        # reset sections if movie/shows have been picked
        if movies or shows or episodes:
            movie_sections = []
            show_sections = []

        return WalkPlan(
            movie_sections,
            show_sections,
            movies,
            shows,
            episodes,
        )

    def find_by_id(self, movie_sections, show_sections):
        if not self.config.id:
            return [None, None, None]

        results = defaultdict(list)
        for id in self.config.id:
            found = (
                self.find_from_sections_by_id(show_sections, id, results)
                if self.config.walk_shows
                else None
            )
            if found:
                continue
            found = (
                self.find_from_sections_by_id(movie_sections, id, results)
                if self.config.walk_movies
                else None
            )
            if found:
                continue
            raise RuntimeError(f"Id '{id}' not found")

        movies = []
        shows = []
        episodes = []
        for mediatype, items in results.items():
            if mediatype == "episode":
                episodes.extend(items)
            elif mediatype == "show":
                shows.extend(items)
            elif mediatype == "movie":
                movies.extend(items)
            else:
                raise RuntimeError(f"Unsupported type: {mediatype}")

        return [movies, shows, episodes]

    @staticmethod
    def find_from_sections_by_id(sections, id, results):
        for section in sections:
            m = section.find_by_id(id)
            if m:
                results[m.type].append(m)
                return True
        return False

    @staticmethod
    def find_from_sections_by_title(sections, names, items):
        if not names:
            return items

        if not items:
            items = []

        for name in names:
            found = False
            for section in sections:
                m = section.find_by_title(name)
                if m:
                    items.append(m)
                    found = True
            if not found:
                raise RuntimeError(f"Show/Movie '{name}' not found")

        return items

    def find_sections(self):
        """
        Build movie and show sections based on library and walk_movies/walk_shows.
        A valid match must be found if such filter is enabled.

        :return: [movie_sections, show_sections]
        """
        if not self.config.library:
            movie_sections = (
                self.plex.movie_sections() if self.config.walk_movies else []
            )
            show_sections = self.plex.show_sections() if self.config.walk_shows else []
            return [movie_sections, show_sections]

        movie_sections = []
        show_sections = []
        for library in self.config.library:
            movie_section = (
                self.plex.movie_sections(library) if self.config.walk_movies else []
            )
            if movie_section:
                movie_sections.extend(movie_section)
                continue
            show_section = (
                self.plex.show_sections(library) if self.config.walk_shows else []
            )
            if show_section:
                show_sections.extend(show_section)
                continue
            raise RuntimeError(f"Library '{library}' not found")

        return [movie_sections, show_sections]


class Walker:
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
        return WalkPlanner(self.plex, self.config).plan()

    @property
    def is_partial(self):
        return self.config.is_partial

    def print_plan(self, print=print):
        if self.plan.movie_sections:
            print(f"Sync Movie sections: {[x.title for x in self.plan.movie_sections]}")

        if self.plan.show_sections:
            print(f"Sync Show sections: {[x.title for x in self.plan.show_sections]}")

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

        for ps in self.get_plex_shows():
            show = self.mf.resolve_any(ps)
            if not show:
                continue
            yield from self.episode_from_show(show)

    def walk_shows(self, shows: Set[Media], title="Processing Shows"):
        if not shows:
            return
        yield from self.progressbar(shows, desc=title)

    def get_plex_episodes(self, episodes) -> Generator[Media, Any, None]:
        it = self.progressbar(episodes, desc="Processing episodes")
        for pe in it:
            guid = PlexGuid(pe.grandparentGuid, "show")
            show = self.mf.resolve_guid(guid)
            if not show:
                continue
            me = self.mf.resolve_any(PlexLibraryItem(pe), show)
            if not me:
                continue

            me.show = show
            yield me

    def media_from_sections(self, sections: List[PlexLibrarySection]) -> Generator[PlexLibraryItem, Any, None]:
        for section in sections:
            with measure_time(f"{section.title} processed"):
                total = len(section)
                it = self.progressbar(
                    section.items(total),
                    total=total,
                    desc=f"Processing {section.title}",
                )
                yield from it

    def media_from_items(self, libtype: str, items: List) -> Generator[PlexLibraryItem, Any, None]:
        it = self.progressbar(items, desc=f"Processing {libtype}s")
        for m in it:
            yield PlexLibraryItem(m, self.plex)

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
            tm = TraktItem(media, trakt=self.trakt)
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
