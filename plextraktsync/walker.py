from typing import List, NamedTuple

from plexapi.library import MovieSection, ShowSection
from plexapi.video import Movie, Show

from plextraktsync.decorators.deprecated import deprecated
from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.decorators.memoize import memoize
from plextraktsync.media import Media, MediaFactory
from plextraktsync.plex_api import PlexApi, PlexLibraryItem, PlexLibrarySection
from plextraktsync.trakt_api import TraktApi


class WalkConfig:
    walk_movies = True
    walk_shows = True
    library = []
    show = []
    movie = []
    id = []

    def __init__(self, movies=True, shows=True):
        self.walk_movies = movies
        self.walk_shows = shows

    def update(self, movies=None, shows=None):
        if movies is not None:
            self.walk_movies = movies
        if shows is not None:
            self.walk_shows = shows

        return self

    def add_library(self, library):
        self.library.append(library)

    def add_id(self, id):
        self.id.append(id)

    def add_show(self, show):
        self.show.append(show)

    def add_movie(self, movie):
        self.movie.append(movie)

    def is_valid(self):
        # Single item provided
        if self.library or self.movie or self.show or self.id:
            return True

        # Full sync of movies or shows
        if self.walk_movies or self.walk_shows:
            return True

        return False


class WalkPlan(NamedTuple):
    movie_sections: List[MovieSection]
    show_sections: List[ShowSection]
    movies: List[Movie]
    shows: List[Show]


class WalkPlanner:
    def __init__(self, plex: PlexApi, config: WalkConfig):
        self.plex = plex
        self.config = config

    def plan(self):
        movie_sections, show_sections = self.find_sections()
        movies, shows = self.find_by_id(movie_sections, show_sections)
        shows = self.find_from_sections_by_title(show_sections, self.config.show, shows)
        movies = self.find_from_sections_by_title(movie_sections, self.config.movie, movies)

        # reset sections if movie/shows have been picked
        movie_sections = [] if movies else movie_sections
        show_sections = [] if shows else show_sections

        return WalkPlan(
            movie_sections,
            show_sections,
            movies,
            shows,
        )

    def find_by_id(self, movie_sections, show_sections):
        if not self.config.id:
            return [None, None]

        movies = []
        shows = []
        for id in self.config.id:
            movie = self.find_from_sections_by_id(movie_sections, id) if self.config.walk_movies else []
            if movie:
                movies.extend(movie)
                continue
            show = self.find_from_sections_by_id(show_sections, id) if self.config.walk_shows else []
            if show:
                shows.extend(show)
                continue
            raise RuntimeError(f"Id '{id}' not found")
        return [movies, shows]

    @staticmethod
    def find_from_sections_by_id(sections, id):
        results = []
        for section in sections:
            m = section.find_by_id(id)
            if m:
                results.append(m)
        return results

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
            movie_sections = self.plex.movie_sections() if self.config.walk_movies else []
            show_sections = self.plex.show_sections() if self.config.walk_shows else []
            return [movie_sections, show_sections]

        movie_sections = []
        show_sections = []
        for library in self.config.library:
            movie_section = self.plex.movie_sections(library) if self.config.walk_movies else []
            if movie_section:
                movie_sections.extend(movie_section)
                continue
            show_section = self.plex.show_sections(library) if self.config.walk_shows else []
            if show_section:
                show_sections.extend(show_section)
                continue
            raise RuntimeError(f"Library '{library}' not found")

        return [movie_sections, show_sections]


class Walker:
    """
    Class dealing with finding and walking library, movies/shows, episodes
    """

    def __init__(self, plex: PlexApi, trakt: TraktApi, mf: MediaFactory, config: WalkConfig, progressbar=None):
        self._progressbar = progressbar
        self.plex = plex
        self.trakt = trakt
        self.mf = mf
        self.config = config

    @property
    @memoize
    def plan(self):
        return WalkPlanner(self.plex, self.config).plan()

    def print_plan(self, print=print):
        if self.plan.movie_sections:
            print(f"Sync Movie sections: {self.plan.movie_sections}")

        if self.plan.show_sections:
            print(f"Sync Show sections: {self.plan.show_sections}")

        if self.plan.movies:
            print(f"Sync Movies: {self.plan.movies}")

        if self.plan.shows:
            print(f"Sync Shows: {self.plan.shows}")

    def get_plex_movies(self):
        """
        Iterate over movie sections unless specific movie is requested
        """
        if self.plan.movies:
            movies = self.media_from_items("movie", self.plan.movies)
        else:
            movies = self.media_from_sections(self.plan.movie_sections)

        yield from movies

    def find_movies(self):
        for plex in self.get_plex_movies():
            movie = self.mf.resolve_any(plex)
            if not movie:
                continue
            yield movie

    def get_plex_shows(self):
        if self.plan.shows:
            shows = self.media_from_items("show", self.plan.shows)
        else:
            shows = self.media_from_sections(self.plex.show_sections())

        yield from shows

    def find_episodes(self):
        for plex in self.get_plex_shows():
            show = self.mf.resolve_any(plex)
            if not show:
                continue
            yield from self.episode_from_show(show)

    def media_from_sections(self, sections: List[PlexLibrarySection], titles: List[str] = None):
        if titles:
            # Filter by matching section names
            sections = [x for x in sections if x.title in titles]

        for section in sections:
            with measure_time(f"{section.title} processed"):
                total = len(section)
                it = self.progressbar(section.items(total), total=total, desc=f"Processing {section.title}")
                yield from it

    def media_from_items(self, libtype: str, items: List):
        it = self.progressbar(items, desc=f"Processing {libtype}s")
        for m in it:
            yield PlexLibraryItem(m)

    @deprecated("No longer used")
    def media_from_titles(self, libtype: str, titles: List[str]):
        it = self.progressbar(titles, desc=f"Processing {libtype}s")
        for title in it:
            search = self.plex.search(title, libtype=libtype)
            yield from search

    def episode_from_show(self, show: Media):
        for pe in show.plex.episodes():
            me = self.mf.resolve_any(pe, show.trakt)
            if not me:
                continue

            me.show = show
            yield me

    def progressbar(self, iterable, **kwargs):
        if self._progressbar:
            pb = self._progressbar(iterable, **kwargs)
            with pb as it:
                yield from it
        else:
            yield from iterable
