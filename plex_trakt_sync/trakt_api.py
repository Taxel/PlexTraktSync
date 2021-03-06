import trakt

from plex_trakt_sync import pytrakt_extensions
from plex_trakt_sync.path import pytrakt_file

trakt.core.CONFIG_PATH = pytrakt_file
import trakt.users
from trakt.errors import OAuthException, ForbiddenException

from plex_trakt_sync.logging import logging
from plex_trakt_sync.decorators import memoize, nocache
from plex_trakt_sync.config import CONFIG


class TraktApi:
    """
    Trakt API class abstracting common data access and dealing with requests cache.
    """

    @property
    @memoize
    @nocache
    def me(self):
        try:
            return trakt.users.User('me')
        except (OAuthException, ForbiddenException) as e:
            logging.fatal("Trakt authentication error: {}".format(str(e)))
            raise e

    @property
    @memoize
    @nocache
    def liked_lists(self):
        if not CONFIG['sync']['liked_lists']:
            return []
        return pytrakt_extensions.get_liked_lists()

    @property
    @memoize
    @nocache
    def watched_movies(self):
        return set(
            map(lambda m: m.trakt, self.me.watched_movies)
        )

    @property
    @memoize
    @nocache
    def movie_collection(self):
        return set(
            map(lambda m: m.trakt, self.me.movie_collection)
        )

    @property
    @memoize
    @nocache
    def watched_shows(self):
        return pytrakt_extensions.allwatched()
