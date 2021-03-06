import trakt
from plex_trakt_sync.path import pytrakt_file

trakt.core.CONFIG_PATH = pytrakt_file
import trakt.users
from trakt.errors import OAuthException, ForbiddenException

from plex_trakt_sync.logging import logging
from plex_trakt_sync.decorators import memoize, nocache


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
