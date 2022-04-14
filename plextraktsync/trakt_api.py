from __future__ import annotations

from time import time
from typing import Union

import trakt
import trakt.movies
import trakt.sync
import trakt.users
from trakt import post
from trakt.errors import ForbiddenException, OAuthException
from trakt.movies import Movie
from trakt.sync import Scrobbler
from trakt.tv import TVEpisode, TVSeason, TVShow

from plextraktsync import pytrakt_extensions
from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.decorators.flatten import flatten_dict
from plextraktsync.decorators.nocache import nocache
from plextraktsync.decorators.rate_limit import rate_limit
from plextraktsync.decorators.time_limit import time_limit
from plextraktsync.factory import factory
from plextraktsync.logging import logger, logging
from plextraktsync.path import pytrakt_file
from plextraktsync.plex_api import PlexGuid, PlexLibraryItem


class ScrobblerProxy:
    """
    Proxy to Scrobbler that handles requsts cache and rate limiting
    """

    def __init__(self, scrobbler: Scrobbler, threshold=80):
        self.scrobbler = scrobbler
        self.threshold = threshold
        self.logger = logging.getLogger("PlexTraktSync.ScrobblerProxy")

    def update(self, progress: float):
        self.logger.debug(f"update({self.scrobbler.media}): {progress}")
        return self._post("start", progress)

    def pause(self, progress: float):
        self.logger.debug(f"pause({self.scrobbler.media}): {progress}")
        return self._post("pause", progress)

    def stop(self, progress: float):
        if progress >= self.threshold:
            self.logger.debug(f"stop({self.scrobbler.media}): {progress}")
            return self._post("stop", progress)
        else:
            self.logger.debug(f"pause({self.scrobbler.media}): {progress}")
            return self._post("pause", progress)

    # Copied method, until upstream is merged
    # https://github.com/moogar0880/PyTrakt/pull/196
    @nocache
    @rate_limit()
    @time_limit()
    @post
    def _post(self, method: str, progress: float):
        self.scrobbler.progress = progress
        uri = f"scrobble/{method}"
        payload = dict(
            progress=self.scrobbler.progress,
            app_version=self.scrobbler.version,
            date=self.scrobbler.date,
        )
        payload.update(self.scrobbler.media.to_json_singular())
        response = yield uri, payload
        yield response


class TraktRatingCollection(dict):
    def __init__(self, trakt: TraktApi):
        super(dict, self).__init__()
        self.trakt = trakt

    def __missing__(self, media_type: str):
        ratings = self.ratings(media_type)
        self[media_type] = ratings

        return ratings

    @flatten_dict
    def ratings(self, media_type: str):
        index = media_type.rstrip("s")
        for r in self.trakt.get_ratings(media_type):
            yield r[index]["ids"]["trakt"], r["rating"]


class TraktApi:
    """
    Trakt API class abstracting common data access and dealing with requests cache.
    """

    def __init__(self, batch_delay=None):
        self.batch_delay = batch_delay
        trakt.core.CONFIG_PATH = pytrakt_file
        trakt.core.session = factory.session()

    @staticmethod
    def device_auth(client_id: str, client_secret: str):
        trakt.core.AUTH_METHOD = trakt.core.DEVICE_AUTH

        return trakt.init(client_id=client_id, client_secret=client_secret, store=True)

    @cached_property
    def batch(self):
        return TraktBatch(self, batch_delay=self.batch_delay)

    @cached_property
    @nocache
    @rate_limit()
    def me(self):
        try:
            return trakt.users.User("me")
        except (OAuthException, ForbiddenException) as e:
            logger.fatal("Trakt authentication error: {}".format(str(e)))
            raise e

    @cached_property
    @nocache
    @rate_limit()
    def liked_lists(self):
        return pytrakt_extensions.get_liked_lists()

    @cached_property
    @nocache
    @rate_limit()
    def watched_movies(self):
        return set(map(lambda m: m.trakt, self.me.watched_movies))

    @cached_property
    @nocache
    @rate_limit()
    def movie_collection(self):
        return self.me.movie_collection

    @cached_property
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

    @cached_property
    def movie_collection_set(self):
        return set(map(lambda m: m.trakt, self.movie_collection))

    @cached_property
    @nocache
    @rate_limit()
    def watched_shows(self):
        return pytrakt_extensions.allwatched()

    @cached_property
    @nocache
    @rate_limit()
    def watchlist_movies(self):
        return self.me.watchlist_movies

    @cached_property
    def ratings(self):
        return TraktRatingCollection(self)

    @nocache
    @rate_limit()
    @time_limit()
    def get_ratings(self, media_type: str):
        return self.me.get_ratings(media_type)

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
        elif m.media_type == "episodes" and show_trakt_id:
            self.watched_shows.add(show_trakt_id, m.season, m.number)
        else:
            raise RuntimeError(f"mark_watched: Unsupported media type: {m.media_type}")

    def add_to_collection(self, m, pm: PlexLibraryItem, batch=False):
        if m.media_type == "movies":
            item = dict(
                title=m.title,
                year=m.year,
                **m.ids,
                **pm.to_json(),
            )
        elif m.media_type == "episodes":
            item = dict(**m.ids, **pm.to_json())
        else:
            raise ValueError(f"Unsupported media type: {m.media_type}")

        if batch:
            self.batch.add_to_collection(m.media_type, item)
        else:
            trakt.sync.add_to_collection(item)

    @nocache
    @rate_limit()
    def collected(self, tm: TVShow):
        return pytrakt_extensions.collected(tm.trakt)

    @nocache
    @rate_limit()
    def lookup(self, tm: TVShow):
        """
        This lookup-table is accessible via lookup[season][episode]
        """
        return pytrakt_extensions.lookup_table(tm)

    def find_by_guid(self, guid: PlexGuid):
        if guid.type == "episode" and guid.is_episode:
            ts = self.search_by_id(
                guid.show_id, id_type=guid.provider, media_type="show"
            )
            lookup = self.lookup(ts)

            return self.find_episode_guid(guid, lookup)

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

        search = trakt.sync.search_by_id(
            media_id, id_type=id_type, media_type=media_type
        )
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
        if media_id[0:2] == "tt" and media_id[2:].isnumeric():
            return True

        # must be numeric
        if not media_id.isnumeric():
            return False

        # must be shorter than 12 numbers
        return len(media_id) < 12

    def find_episode_guid(self, guid: PlexGuid, lookup):
        """
        Find Trakt Episode from Guid of Plex Episode
        """
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
    def __init__(self, trakt: TraktApi, batch_delay=None):
        self.trakt = trakt
        self.batch_delay = batch_delay
        self.collection = {}
        self.last_sent_time = 0

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
                logger.debug(f"Updated Trakt collection: {result}")
        finally:
            self.collection.clear()
            self.last_sent_time = time()

    def queue_size(self):
        size = 0
        for media_type in self.collection:
            size += len(self.collection[media_type])

        return size

    def flush(self, force=False):
        """
        Flush the queue every batch_delay seconds
        """
        if not self.batch_delay and force is False:
            return
        elapsed = time() - self.last_sent_time
        if elapsed >= self.batch_delay or force is True:
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
