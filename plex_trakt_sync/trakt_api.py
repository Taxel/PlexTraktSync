import trakt

from plex_trakt_sync import pytrakt_extensions
from plex_trakt_sync.path import pytrakt_file

trakt.core.CONFIG_PATH = pytrakt_file
import trakt.users
import trakt.sync
import trakt.movies
from trakt.errors import OAuthException, ForbiddenException

from plex_trakt_sync.logging import logging
from plex_trakt_sync.decorators import memoize, nocache, rate_limit
from plex_trakt_sync.config import CONFIG


class TraktApi:
    """
    Trakt API class abstracting common data access and dealing with requests cache.
    """

    @property
    @memoize
    @nocache
    @rate_limit()
    def me(self):
        try:
            return trakt.users.User('me')
        except (OAuthException, ForbiddenException) as e:
            logging.fatal("Trakt authentication error: {}".format(str(e)))
            raise e

    @property
    @memoize
    @nocache
    @rate_limit()
    def liked_lists(self):
        if not CONFIG['sync']['liked_lists']:
            return []
        return pytrakt_extensions.get_liked_lists()

    @property
    @memoize
    @nocache
    @rate_limit()
    def watched_movies(self):
        return set(
            map(lambda m: m.trakt, self.me.watched_movies)
        )

    @property
    @memoize
    @nocache
    @rate_limit()
    def movie_collection(self):
        return set(
            map(lambda m: m.trakt, self.me.movie_collection)
        )

    @property
    @memoize
    @nocache
    @rate_limit()
    def watched_shows(self):
        return pytrakt_extensions.allwatched()

    @property
    @memoize
    @nocache
    @rate_limit()
    def watchlist_movies(self):
        if not CONFIG['sync']['watchlist']:
            return []

        return list(
            map(lambda m: m.trakt, self.me.watchlist_movies)
        )

    @property
    @memoize
    @nocache
    @rate_limit()
    def movie_ratings(self):
        return self.me.get_ratings(media_type='movies')

    @property
    @memoize
    def ratings(self):
        ratings = {}
        for r in self.movie_ratings:
            ratings[r['movie']['ids']['slug']] = r['rating']

        return ratings

    def find_movie(self, movie):
        try:
            search = trakt.sync.search_by_id(movie.id, id_type=movie.provider)
        except ValueError as e:
            # ValueError: search_type must be one of ('trakt', 'trakt-movie', 'trakt-show', 'trakt-episode', 'trakt-person', 'imdb', 'tmdb', 'tvdb')
            raise e
        # look for the first movie in the results
        for m in search:
            if type(m) is trakt.movies.Movie:
                return m

        return None
