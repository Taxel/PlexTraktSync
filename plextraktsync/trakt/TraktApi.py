from __future__ import annotations

from typing import TYPE_CHECKING

import trakt
import trakt.movies
import trakt.sync
import trakt.users
from deprecated import deprecated
from trakt.errors import ForbiddenException, OAuthException

from plextraktsync import pytrakt_extensions
from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.decorators.flatten import flatten_list
from plextraktsync.decorators.rate_limit import rate_limit
from plextraktsync.decorators.retry import retry
from plextraktsync.decorators.time_limit import time_limit
from plextraktsync.factory import factory, logger
from plextraktsync.path import pytrakt_file
from plextraktsync.trakt.ScrobblerProxy import ScrobblerProxy
from plextraktsync.trakt.TraktLookup import TraktLookup
from plextraktsync.trakt.TraktRatingCollection import TraktRatingCollection
from plextraktsync.trakt.types import TraktMedia

if TYPE_CHECKING:
    from typing import List, Optional, Union

    from trakt.movies import Movie
    from trakt.tv import TVEpisode, TVShow

    from plextraktsync.plex.PlexGuid import PlexGuid
    from plextraktsync.plex_api import PlexLibraryItem
    from plextraktsync.trakt.TraktBatch import TraktBatch


class TraktApi:
    """
    Trakt API class abstracting common data access and dealing with requests cache.
    """

    def __init__(self):
        trakt.core.CONFIG_PATH = pytrakt_file
        trakt.core.session = factory.session

    @staticmethod
    def device_auth(client_id: str, client_secret: str):
        trakt.core.AUTH_METHOD = trakt.core.DEVICE_AUTH

        return trakt.init(client_id=client_id, client_secret=client_secret, store=True)

    @cached_property
    def batch_collection_add(self):
        return self.trakt_batch("collection", add=True)

    @cached_property
    def batch_collection_del(self):
        return self.trakt_batch("collection", add=False)

    @cached_property
    def batch_watchlist_add(self):
        return self.trakt_batch("watchlist", add=True)

    @cached_property
    def batch_watchlist_del(self):
        return self.trakt_batch("watchlist", add=False)

    @cached_property
    @rate_limit()
    @retry()
    def me(self):
        try:
            return trakt.users.User("me")
        except (OAuthException, ForbiddenException) as e:
            logger.fatal(f"Trakt authentication error: {str(e)}")
            raise e

    @cached_property
    @rate_limit()
    @retry()
    @flatten_list
    def liked_lists(self):
        for item in self.me.get_liked_lists("lists", limit=1000):
            yield {
                'listname': item['list']['name'],
                'listid': item['list']['ids']['trakt'],
            }

    @cached_property
    @rate_limit()
    @retry()
    def watched_movies(self):
        return set(map(lambda m: m.trakt, self.me.watched_movies))

    @cached_property
    @rate_limit()
    @retry()
    def movie_collection(self):
        return self.me.movie_collection

    @cached_property
    @rate_limit()
    @retry()
    def show_collection(self):
        return self.me.show_collection

    @rate_limit()
    @time_limit()
    @retry()
    def remove_from_library(self, media: TraktMedia):
        media.remove_from_library()

    @cached_property
    def movie_collection_set(self):
        return set(map(lambda m: m.trakt, self.movie_collection))

    @cached_property
    @rate_limit()
    @retry()
    def watched_shows(self):
        return pytrakt_extensions.allwatched()

    @cached_property
    @rate_limit()
    @retry()
    def collected_shows(self):
        return pytrakt_extensions.allcollected()

    @cached_property
    @rate_limit()
    @retry()
    def watchlist_movies(self) -> List[Movie]:
        return self.me.watchlist_movies

    @cached_property
    @rate_limit()
    @retry()
    def watchlist_shows(self) -> List[TVShow]:
        return self.me.watchlist_shows

    @cached_property
    def ratings(self):
        return TraktRatingCollection(self)

    def rating(self, m) -> Optional[int]:
        """
        The trakt api (Python module) is inconsistent:
        - Movie has "rating" property, while TVShow does not
        However, the Movie property is always None.
        So fetch for all types.
        """
        if m.media_type in ["movies", "shows", "episodes"]:
            r = self.ratings[m.media_type]
            return r.get(m.trakt, None)
        else:
            raise ValueError(f"Unsupported type: {m.media_type}")

    @rate_limit()
    @retry()
    def get_ratings(self, media_type: str):
        return self.me.get_ratings(media_type)

    @rate_limit()
    @time_limit()
    @retry()
    def rate(self, m, rating):
        m.rate(rating)

    @staticmethod
    def scrobbler(media: Union[Movie, TVEpisode], threshold=80) -> ScrobblerProxy:
        scrobbler = media.scrobble(0, None, None)
        return ScrobblerProxy(scrobbler, threshold)

    @rate_limit()
    @time_limit()
    @retry()
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
            self.batch_collection_add.add_to_items(m.media_type, item)
        else:
            trakt.sync.add_to_collection(item)

    def add_to_watchlist(self, m, batch=False):
        if m.media_type in ["movies", "shows"]:
            item = dict(
                title=m.title,
                year=m.year,
                **m.ids,
            )
        else:
            raise ValueError(f"Unsupported media type for watchlist: {m.media_type}")
        if batch:
            self.batch_watchlist_add.add_to_items(m.media_type, item)
        else:
            trakt.sync.add_to_watchlist(item)

    def remove_from_watchlist(self, m, batch=False):
        if m.media_type in ["movies", "shows"]:
            item = dict(
                title=m.title,
                year=m.year,
                **m.ids,
            )
        else:
            raise ValueError(f"Unsupported media type for watchlist: {m.media_type}")

        if batch:
            self.batch_watchlist_del.add_to_items(m.media_type, item)
        else:
            trakt.sync.remove_from_watchlist(item)

    def find_by_guid(self, guid: PlexGuid):
        if guid.type == "episode" and guid.is_episode:
            ts: TVShow = self.search_by_id(
                guid.show_id, id_type=guid.provider, media_type="show"
            )
            if ts:
                lookup = TraktLookup(ts)

                return self.find_episode_guid(guid, lookup)
        else:
            return self.search_by_id(guid.id, id_type=guid.provider, media_type=guid.type)

    @rate_limit()
    @retry()
    def search_by_id(self, media_id: str, id_type: str, media_type: str) -> Optional[Union[TVShow, Movie]]:
        if id_type == "tvdb" and media_type == "movie":
            # Skip invalid search.
            # The Trakt API states that tvdb is only for shows and episodes:
            # https://trakt.docs.apiary.io/#reference/search/id-lookup/get-id-lookup-results
            logger.debug("tvdb does not support movie provider")
            return None
        if media_type == "season":
            # Search by season is missing
            # https://github.com/Taxel/PlexTraktSync/issues/1117#issuecomment-1286884897
            logger.debug("trakt does not support search by season")
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

    def find_episode_guid(self, guid: PlexGuid, lookup: TraktLookup):
        """
        Find Trakt Episode from Guid of Plex Episode
        """
        te = lookup.from_guid(guid)
        if te:
            return te

        logger.debug(f"Retry using search for specific Plex Episode {guid.guid}")
        if not guid.is_episode:
            return self.find_by_guid(guid)
        return None

    @deprecated("No longer in use")
    def flush(self):
        """
        Submit all pending data
        """
        self.batch_collection_add.flush(force=True)
        self.batch_collection_del.flush(force=True)
        self.batch_watchlist_add.flush(force=True)
        self.batch_watchlist_del.flush(force=True)

    @staticmethod
    def trakt_batch(*args, **kwargs) -> TraktBatch:
        return factory.trakt_batch(*args, **kwargs)
