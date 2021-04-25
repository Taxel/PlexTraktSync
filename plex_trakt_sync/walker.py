from typing import List

from plex_trakt_sync.media import MediaFactory
from plex_trakt_sync.plex_api import PlexApi


class Walker:
    """
    Class dealing with finding and walking library, movies/shows, episodes
    """

    def __init__(self, plex: PlexApi, mf: MediaFactory):
        self.plex = plex
        self.mf = mf
        self.library = []
        self.show = []
        self.movie = []

    def add_library(self, library):
        self.library.append(library)

    def add_show(self, show):
        self.show.append(show)

    def add_movie(self, movie):
        self.movie.append(movie)

    def find_movies(self):
        """
        Iterate over movie sections unless specific movie is requested
        """
        if self.movie:
            movies = self.media_from_titles("movie", self.movie)
        else:
            movies = self.media_from_sections(self.plex.movie_sections(), self.library)

        for plex in movies:
            movie = self.mf.resolve(plex)
            if not movie:
                continue
            yield movie

    def find_episodes(self):
        if self.show:
            shows = self.media_from_titles("show", self.show)
        else:
            shows = self.media_from_sections(self.plex.show_sections(), self.library)

        for plex in shows:
            show = self.mf.resolve(plex)
            if not show:
                continue
            yield show

    def media_from_sections(self, sections, titles: List[str]):
        if titles:
            # Filter by matching section names
            sections = [x for x in sections if x.title in titles]

        for section in sections:
            for pm in section.items():
                yield pm

    def media_from_titles(self, libtype: str, titles: List[str]):
        for title in titles:
            search = self.plex.search(title, libtype=libtype)
            yield from search

    def from_show_titles(self, movie):
        pass

    def from_show_libraries(self, library):
        pass
