from typing import List

from plex_trakt_sync.decorators.measure_time import measure_time
from plex_trakt_sync.media import Media, MediaFactory
from plex_trakt_sync.plex_api import PlexApi, PlexLibrarySection
from plex_trakt_sync.trakt_api import TraktApi


class Walker:
    """
    Class dealing with finding and walking library, movies/shows, episodes
    """

    def __init__(self, plex: PlexApi, trakt: TraktApi, mf: MediaFactory, progressbar=None, movies=True, shows=True):
        self._progressbar = progressbar
        self.plex = plex
        self.trakt = trakt
        self.mf = mf
        self.walk_movies = movies
        self.walk_shows = shows
        self.library = []
        self.show = []
        self.movie = []

    def add_library(self, library):
        self.library.append(library)

    def add_show(self, show):
        self.show.append(show)
        self.walk_movies = False

    def add_movie(self, movie):
        self.movie.append(movie)
        self.walk_shows = False

    def is_valid(self):
        # Single item provided
        if self.library or self.movie or self.show:
            return True

        # Full sync of movies or shows
        if self.walk_movies or self.walk_shows:
            return True

        return False

    def walk_details(self, print=print):
        print(f"Sync Movies: {self.walk_movies}")
        print(f"Sync Shows: {self.walk_shows}")
        if self.library:
            print(f"Walk libraries: {self.library}")
        if self.show:
            print(f"Walk Shows: {self.show}")
        if self.movie:
            print(f"Walk Movies: {self.movie}")

    def get_plex_movies(self):
        """
        Iterate over movie sections unless specific movie is requested
        """
        if not self.walk_movies:
            return

        if self.movie:
            movies = self.media_from_titles("movie", self.movie)
        else:
            movies = self.media_from_sections(self.plex.movie_sections(), self.library)

        yield from movies

    def find_movies(self):
        for plex in self.get_plex_movies():
            movie = self.mf.resolve_any(plex)
            if not movie:
                continue
            yield movie

    def get_plex_shows(self):
        if not self.walk_shows:
            return

        if self.show:
            shows = self.media_from_titles("show", self.show)
        else:
            shows = self.media_from_sections(self.plex.show_sections(), self.library)

        yield from shows

    def find_episodes(self):
        for plex in self.get_plex_shows():
            show = self.mf.resolve_any(plex)
            if not show:
                continue
            yield from self.episode_from_show(show)

    def media_from_sections(self, sections: List[PlexLibrarySection], titles: List[str]):
        if titles:
            # Filter by matching section names
            sections = [x for x in sections if x.title in titles]

        for section in sections:
            with measure_time(f"{section.title} processed"):
                total = len(section)
                it = self.progressbar(section.items(total), total=total, desc=f"Processing {section.title}")
                yield from it

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
