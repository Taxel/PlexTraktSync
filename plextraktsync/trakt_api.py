from typing import Union

import trakt
import trakt.movies
import trakt.sync
import trakt.users
from trakt.core import load_config
from trakt.errors import ForbiddenException, OAuthException
from trakt.movies import Movie
from trakt.sync import Scrobbler
from trakt.tv import TVEpisode, TVSeason, TVShow

from plextraktsync import pytrakt_extensions
from plextraktsync.decorators.memoize import memoize
from plextraktsync.decorators.nocache import nocache
from plextraktsync.decorators.rate_limit import rate_limit
from plextraktsync.decorators.time_limit import time_limit
from plextraktsync.factory import factory
from plextraktsync.logging import logger
from plextraktsync.path import pytrakt_file
from plextraktsync.plex_api import PlexGuid, PlexLibraryItem


class ScrobblerProxy:
    """
    Proxy to Scrobbler that handles requsts cache and rate limiting
    """

    def __init__(self, scrobbler: Scrobbler, threshold=80):
        self.scrobbler = scrobbler
        self.threshold = threshold

    @nocache
    @rate_limit()
    @time_limit()
    def update(self, progress: float):
        self.scrobbler.update(progress)

    @nocache
    @rate_limit()
    @time_limit()
    def pause(self):
        self.scrobbler.pause()

    @nocache
    @rate_limit()
    @time_limit()
    def stop(self, progress: float):
        if progress >= self.threshold:
            self.scrobbler.stop()
        else:
            self.scrobbler.pause()


class TraktApi:
    """
    Trakt API class abstracting common data access and dealing with requests cache.
    """

    def __init__(self, batch_size=None):
        self.batch = TraktBatch(self, batch_size=batch_size)
        trakt.core.CONFIG_PATH = pytrakt_file
        trakt.core.session = factory.session()
        load_config()

    @staticmethod
    def device_auth(client_id: str, client_secret: str):
        trakt.core.AUTH_METHOD = trakt.core.DEVICE_AUTH

        return trakt.init(client_id=client_id, client_secret=client_secret, store=True)

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
    @rate_limit()
    @time_limit()
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
        return self.me.watchlist_movies

    @property
    @memoize
    @nocache
    @rate_limit()
    def movie_ratings(self):
        ratings = {}
        for r in self.me.get_ratings(media_type='movies'):
            ratings[r['movie']['ids']['trakt']] = r['rating']
        return ratings

    @property
    @memoize
    @nocache
    @rate_limit()
    def episode_ratings(self):
        ratings = {}
        for r in self.me.get_ratings(media_type='episodes'):
            ratings[r['episode']['ids']['trakt']] = r['rating']
        return ratings

    @nocache
    @rate_limit()
    @time_limit()
    def rate(self, m, rating):
        m.rate(rating)

    @staticmethod
    def scrobbler(media: Union[Movie, TVEpisode], threshold=80) -> ScrobblerProxy:
        scrobbler = media.scrobble(0, None, None)
        return ScrobblerProxy(scrobbler, threshold)

    @nocache
    @rate_limit()
    @time_limit()
    def mark_watched(self, m, time, show_trakt_id=None):
        m.mark_as_seen(time)
        if m.media_type == "movies":
            self.watched_movies.add(m.trakt)
        if m.media_type == "episodes" and show_trakt_id:
            self.watched_shows.add(show_trakt_id, m.season, m.number)

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
    def find_by_guid(self, guid: PlexGuid):
        if guid.type == "episode" and guid.is_episode:
            ts = self.search_by_id(guid.show_id, id_type=guid.provider, media_type="show")
            return self.find_episode_guid(ts, guid)

        return self.search_by_id(guid.id, id_type=guid.provider, media_type=guid.type)

    @rate_limit()
    def search_by_id(self, media_id: str, id_type: str, media_type: str):
        if id_type == "tvdb" and media_type == "movie":
            # Skip invalid search.
            # The Trakt API states that tvdb is only for shows and episodes:
            # https://trakt.docs.apiary.io/#reference/search/id-lookup/get-id-lookup-results
            logger.debug("tvdb does not support movie provider")
            return None

        if not self.valid_trakt_id(media_id):
            logger.error(f"Ignoring invalid id: '{media_id}'")

            return None

        search = trakt.sync.search_by_id(media_id, id_type=id_type, media_type=media_type)
        # look for the first wanted type in the results
        # NOTE: this is not needed, kept around for caution
        for m in search:
            if m.media_type != f"{media_type}s":
                logger.error(
                    f"Internal error, wrong media type: {m.media_type}. Please report this to PlexTraktSync developers"
                )
                continue
            return m

        return None

    @staticmethod
    def valid_trakt_id(media_id: str):
        """
        to prevent sending junk to trakt.tv,
        validate that the id is valid for trakt
        """
        # imdb: tt + numbers
        if media_id[0:2] == 'tt' and media_id[2:].isnumeric():
            return True

        # must be numeric
        if not media_id.isnumeric():
            return False

        # must be shorter than 12 numbers
        return len(media_id) < 12

    def find_episode_guid(self, tm: TVShow, guid: PlexGuid, lookup=None):
        """
        Find Trakt Episode from Guid of Plex Episode
        """
        lookup = lookup if lookup else self.lookup(tm)
        try:
            return lookup[guid.pm.season_number][guid.pm.episode_number].instance
        except KeyError:
            # Retry using search for specific Plex Episode
            logger.warning("Retry using search for specific Plex Episode")
            if not guid.is_episode:
                return self.find_by_guid(guid)
            return None

    def flush(self):
        """
        Submit all pending data
        """
        self.batch.submit_collection()


class TraktBatch:
    def __init__(self, trakt: TraktApi, batch_size=None):
        self.trakt = trakt
        self.batch_size = batch_size
        self.collection = {}

    @nocache
    @rate_limit()
    @time_limit()
    def submit_collection(self):
        if self.queue_size() == 0:
            return

        try:
            result = self.trakt_sync_collection(self.collection)
            result = self.remove_empty_values(result.copy())
            if result:
                logger.info(f"Updated Trakt collection: {result}")
        finally:
            self.collection.clear()

    def queue_size(self):
        size = 0
        for media_type in self.collection:
            size += len(self.collection[media_type])

        return size

    def flush(self):
        """
        Flush the queue if it's bigger than batch_size
        """
        if not self.batch_size:
            return

        if self.queue_size() >= self.batch_size:
            self.submit_collection()

    def add_to_collection(self, media_type: str, item):
        """
        Add item of media_type to collection
        """
        if media_type not in self.collection:
            self.collection[media_type] = []

        self.collection[media_type].append(item)
        self.flush()

    @staticmethod
    def trakt_sync_collection(media_object):
        return trakt.sync.add_to_collection(media_object)

    @staticmethod
    def remove_empty_values(result):
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
