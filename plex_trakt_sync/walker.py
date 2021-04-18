class Walker:
    """
    Class dealing with finding and walking library, movies/shows, episodes
    """

    def __init__(self):
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
        pass

    def find_episodes(self):
        pass
