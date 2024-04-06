from __future__ import annotations


class WalkConfig:
    walk_movies = True
    walk_shows = True
    walk_watchlist = True
    library: list[str] = []
    show: list[str] = []
    movie: list[str] = []
    id: list[str] = []

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

    def add_library(self, library: str):
        self.library.append(library)

    def add_id(self, id: str):
        self.id.append(id)

    def add_show(self, show: str):
        self.show.append(show)

    def add_movie(self, movie: str):
        self.movie.append(movie)

    @property
    def is_partial(self):
        """
        Returns true if partial library walk is performed.
        Due to the way watchlist is filled, watchlists should only be updated on full walk.
        """
        # Single item provided
        if self.library or self.movie or self.show or self.id:
            return True

        # Must sync both movies and shows to be full sync
        return not self.walk_movies or not self.walk_shows

    @property
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
