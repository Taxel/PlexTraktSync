from typing import Union
import trakt

from plex_trakt_sync import pytrakt_extensions
from plex_trakt_sync.path import pytrakt_file
from plex_trakt_sync.plex_api import PlexLibraryItem

trakt.core.CONFIG_PATH = pytrakt_file
import trakt.users
import trakt.sync
import trakt.movies
from trakt.movies import Movie
from trakt.tv import TVShow, TVSeason, TVEpisode
from trakt.errors import OAuthException, ForbiddenException
from trakt.sync import Scrobbler

from plex_trakt_sync.logging import logger
from plex_trakt_sync.decorators import memoize, nocache, rate_limit
from plex_trakt_sync.config import CONFIG

TRAKT_POST_DELAY = 1.1


class ScrobblerProxy:
    """
    Proxy to Scrobbler that handles requsts cache and rate limiting
    """

    def __init__(self, scrobbler: Scrobbler):
        self.scrobbler = scrobbler

    @nocache
    @rate_limit(delay=TRAKT_POST_DELAY)
    def update(self, progress: float):
        self.scrobbler.update(progress)

    @nocache
    @rate_limit(delay=TRAKT_POST_DELAY)
    def pause(self):
        self.scrobbler.pause()

    @nocache
    @rate_limit(delay=TRAKT_POST_DELAY)
    def stop(self):
        self.scrobbler.stop()


class TraktApi:
    """
    Trakt API class abstracting common data access and dealing with requests cache.
    """

    def __init__(self):
        self.batch = TraktBatch(self)

    @property
    @memoize
    @nocache
    @rate_limit()
    def me(self):
        try:
            return trakt.users.User('me')
        except (OAuthException, ForbiddenException) as e:
            logger.fatal("Trakt authentication error: {}".format(str(e)))
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
        return self.me.movie_collection

    @property
    @memoize
    @nocache
    @rate_limit()
    def show_collection(self):
        return self.me.show_collection

    @nocache
    @rate_limit(delay=TRAKT_POST_DELAY)
    def remove_from_library(self, media: Union[Movie, TVShow, TVSeason, TVEpisode]):
        if not isinstance(media, (Movie, TVShow, TVSeason, TVEpisode)):
            raise ValueError("Must be valid media type")
        media.remove_from_library()

    @property
    @memoize
    def movie_collection_set(self):
        return set(
            map(lambda m: m.trakt, self.movie_collection)
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

    def rating(self, m):
        if m.slug in self.ratings:
            return int(self.ratings[m.slug])

        return None

    @nocache
    @rate_limit(delay=TRAKT_POST_DELAY)
    def rate(self, m, rating):
        m.rate(rating)

    def scrobbler(self, media: Union[Movie, TVEpisode]) -> ScrobblerProxy:
        scrobbler = media.scrobble(0, None, None)
        return ScrobblerProxy(scrobbler)

    @nocache
    @rate_limit(delay=TRAKT_POST_DELAY)
    def mark_watched(self, m, time):
        m.mark_as_seen(time)

    def add_to_collection(self, m, pm: PlexLibraryItem):
        if m.media_type == "movies":
            item = dict(
                title=m.title,
                year=m.year,
                **m.ids,
                **pm.to_json(),
            )
        elif m.media_type == "episodes":
            item = dict(
                **m.ids,
                **pm.to_json()
            )
        else:
            raise ValueError(f"Unsupported media type: {m.media_type}")

        self.batch.add_to_collection(m.media_type, item)

    @memoize
    @nocache
    @rate_limit()
    def collected(self, tm: TVShow):
        return pytrakt_extensions.collected(tm.trakt)

    @memoize
    @nocache
    @rate_limit()
    def lookup(self, tm: TVShow):
        """
        This lookup-table is accessible via lookup[season][episode]
        """
        return pytrakt_extensions.lookup_table(tm)

    @memoize
    @rate_limit()
    def find_by_media(self, pm: PlexLibraryItem, media_id=None):
        media_id = media_id if media_id is not None else pm.id
        try:
            search = trakt.sync.search_by_id(media_id, id_type=pm.provider, media_type=pm.type)
        except ValueError as e:
            # Search_type must be one of ('trakt', ..., 'imdb', 'tmdb', 'tvdb')
            raise ValueError(f"Invalid id_type: '{pm.provider}', guid: '{pm.guid}', guids: '{pm.guids}': {e}") from e
        # look for the first wanted type in the results
        for m in search:
            if m.media_type == pm.media_type:
                return m

        return None

    def flush(self):
        """
        Submit all pending data
        """
        self.batch.submit_collection()


class TraktBatch:
    def __init__(self, trakt: TraktApi):
        self.trakt = trakt
        self.collection = {}

    @nocache
    @rate_limit(delay=TRAKT_POST_DELAY)
    def submit_collection(self):
        if not len(self.collection):
            return None

        try:
            result = trakt.sync.add_to_collection(self.collection)
            result = self.remove_empty_values(result)
            if result:
                logger.info(f"Updated Trakt collection: {result}")
        finally:
            self.collection.clear()

    def add_to_collection(self, media_type: str, item):
        """
        Add item of media_type to collection
        """
        if media_type not in self.collection:
            self.collection[media_type] = []

        self.collection[media_type].append(item)

    def remove_empty_values(self, result):
        """
        Update result to remove empty changes.
        This makes diagnostic printing cleaner if we don't print "changed: 0"
        """
        for change_type in ["added", "existing", "updated"]:
            for media_type, value in result[change_type].copy().items():
                if value == 0:
                    del result[change_type][media_type]
            if len(result[change_type]) == 0:
                del result[change_type]

        for media_type, items in result["not_found"].copy().items():
            if len(items) == 0:
                del result["not_found"][media_type]

        if len(result["not_found"]) == 0:
            del result["not_found"]

        if len(result) == 0:
            return None

        return result
