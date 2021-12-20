from collections import defaultdict
from typing import List, NamedTuple

from plexapi.video import Episode, Movie, Show

from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.decorators.memoize import memoize
from plextraktsync.media import Media, MediaFactory
from plextraktsync.plex_api import PlexApi, PlexGuid, PlexLibraryItem, PlexLibrarySection
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
        movies = self.find_from_sections_by_title(movie_sections, self.config.movie, movies)

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
            found = self.find_from_sections_by_id(show_sections, id, results) if self.config.walk_shows else None
            if found:
                continue
            found = self.find_from_sections_by_id(movie_sections, id, results) if self.config.walk_movies else None
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
                raise RuntimeError(f"Unsupported type: {m.type}")

        return [movies, shows, episodes]

    @staticmethod
    def find_from_sections_by_id(sections, id, results):
        found = False
        for section in sections:
            m = section.find_by_id(id)
            if m:
                results[m.type].append(m)
                found = True
        return found

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

        if self.plan.episodes:
            print(f"Sync Episodes: {self.plan.episodes}")

    def get_plex_movies(self):
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

    def find_movies(self):
        for plex in self.get_plex_movies():
            movie = self.mf.resolve_any(plex)
            if not movie:
                continue
            yield movie

    def get_plex_shows(self):
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

    def get_plex_episodes(self, episodes):
        it = self.progressbar(episodes, desc=f"Processing episodes")
        for pe in it:
            guid = PlexGuid(pe.grandparentGuid, "show")
            show = self.mf.resolve_guid(guid)
            if not show:
                continue
            me = self.mf.resolve_any(PlexLibraryItem(pe), show.trakt)
            if not me:
                continue

            me.show = show
            yield me

    def media_from_sections(self, sections: List[PlexLibrarySection]):
        for section in sections:
            with measure_time(f"{section.title} processed"):
                total = len(section)
                it = self.progressbar(section.items(total), total=total, desc=f"Processing {section.title}")
                yield from it

    def media_from_items(self, libtype: str, items: List):
        it = self.progressbar(items, desc=f"Processing {libtype}s")
        for m in it:
            yield PlexLibraryItem(m)

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
