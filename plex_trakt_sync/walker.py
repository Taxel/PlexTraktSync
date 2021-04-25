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
            it = self.from_movie_titles(self.movie)
        else:
            it = self.from_movie_libraries(self.library)

        for pm in it:
            m = self.mf.resolve(pm)
            if not m:
                continue
            yield m

    def from_movie_titles(self, titles):
        for title in titles:
            search = self.plex.search(title, libtype="movie")
            yield from search

    def from_movie_libraries(self, titles):
        for section in self.movie_sections(titles):
            for pm in section.items():
                yield pm

    def movie_sections(self, titles):
        """
        Return movie sections, optionally filter only matching section names
        """
        sections = self.plex.movie_sections()
        if titles:
            # Filter by matching section names
            sections = [x for x in sections if x.title in titles]
        return sections

    def find_episodes(self):
        pass
