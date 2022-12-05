from __future__ import annotations

from collections import defaultdict
from time import time
from typing import List, Optional, Union

import trakt
import trakt.movies
import trakt.sync
import trakt.users
from trakt.errors import ForbiddenException, OAuthException
from trakt.movies import Movie
from trakt.sync import Scrobbler
from trakt.tv import TVEpisode, TVSeason, TVShow

from plextraktsync import pytrakt_extensions
from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.decorators.flatten import flatten_dict, flatten_list
from plextraktsync.decorators.nocache import nocache
from plextraktsync.decorators.rate_limit import rate_limit
from plextraktsync.decorators.retry import retry
from plextraktsync.decorators.time_limit import time_limit
from plextraktsync.factory import factory, logger, logging
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
        return self.scrobbler.update(progress)

    def pause(self, progress: float):
        self.logger.debug(f"pause({self.scrobbler.media}): {progress}")
        return self.scrobbler.pause(progress)

    def stop(self, progress: float):
        if progress >= self.threshold:
            self.logger.debug(f"stop({self.scrobbler.media}): {progress}")
            return self.scrobbler.stop(progress)
        else:
            self.logger.debug(f"pause({self.scrobbler.media}): {progress}")
            return self.scrobbler.pause(progress)


class TraktRatingCollection(dict):
    def __init__(self, trakt: TraktApi):
        super().__init__()
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


class TraktItem:
    def __init__(self, item: Union[Movie, TVShow, TVSeason, TVEpisode], trakt: TraktApi = None):
        self.item = item
        self.trakt = trakt

    @cached_property
    def type(self):
        """
        Return "movie", "show", "season", "episode"
        """
        # NB: TVSeason does not have "media_type" property
        return self.item.media_type[:-1]


class TraktApi:
    """
    Trakt API class abstracting common data access and dealing with requests cache.
    """

    def __init__(self, batch_delay=None):
        self.batch_delay = batch_delay
        trakt.core.CONFIG_PATH = pytrakt_file
        trakt.core.session = factory.session

    @staticmethod
    def device_auth(client_id: str, client_secret: str):
        trakt.core.AUTH_METHOD = trakt.core.DEVICE_AUTH

        return trakt.init(client_id=client_id, client_secret=client_secret, store=True)

    @cached_property
    def batch_collection_add(self):
        return TraktBatch(self, "collection", add=True, batch_delay=self.batch_delay)

    @cached_property
    def batch_collection_del(self):
        return TraktBatch(self, "collection", add=False, batch_delay=self.batch_delay)

    @cached_property
    def batch_watchlist_add(self):
        return TraktBatch(self, "watchlist", add=True, batch_delay=self.batch_delay)

    @cached_property
    def batch_watchlist_del(self):
        return TraktBatch(self, "watchlist", add=False, batch_delay=self.batch_delay)

    @cached_property
    @nocache
    @rate_limit()
    @retry()
    def me(self):
        try:
            return trakt.users.User("me")
        except (OAuthException, ForbiddenException) as e:
            logger.fatal(f"Trakt authentication error: {str(e)}")
            raise e

    @cached_property
    @nocache
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
    @nocache
    @rate_limit()
    @retry()
    def watched_movies(self):
        return set(map(lambda m: m.trakt, self.me.watched_movies))

    @cached_property
    @nocache
    @rate_limit()
    @retry()
    def movie_collection(self):
        return self.me.movie_collection

    @cached_property
    @nocache
    @rate_limit()
    @retry()
    def show_collection(self):
        return self.me.show_collection

    @nocache
    @rate_limit()
    @time_limit()
    @retry()
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
    @retry()
    def watched_shows(self):
        return pytrakt_extensions.allwatched()

    @cached_property
    @nocache
    @rate_limit()
    @retry()
    def collected_shows(self):
        return pytrakt_extensions.allcollected()

    @cached_property
    @nocache
    @rate_limit()
    @retry()
    def watchlist_movies(self) -> List[Movie]:
        return self.me.watchlist_movies

    @cached_property
    @nocache
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

    @nocache
    @rate_limit()
    @retry()
    def get_ratings(self, media_type: str):
        return self.me.get_ratings(media_type)

    @nocache
    @rate_limit()
    @time_limit()
    @retry()
    def rate(self, m, rating):
        m.rate(rating)

    @staticmethod
    def scrobbler(media: Union[Movie, TVEpisode], threshold=80) -> ScrobblerProxy:
        scrobbler = media.scrobble(0, None, None)
        return ScrobblerProxy(scrobbler, threshold)

    @nocache
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

    def flush(self):
        """
        Submit all pending data
        """
        self.batch_collection_add.flush(force=True)
        self.batch_collection_del.flush(force=True)
        self.batch_watchlist_add.flush(force=True)
        self.batch_watchlist_del.flush(force=True)


class TraktBatch:
    def __init__(self, trakt: TraktApi, name: str, add: bool, batch_delay=None):
        if name not in ["collection", "watchlist"]:
            raise ValueError(f"TraktBatch name not allowed: {name}")
        self.name = name
        self.add = add
        self.trakt = trakt
        self.batch_delay = batch_delay
        self.items = defaultdict(list)
        self.last_sent_time = 0

    @nocache
    @rate_limit()
    @time_limit()
    @retry()
    def submit(self):
        try:
            result = self.trakt_sync(self.items)
            result = self.remove_empty_values(result.copy())
            if result:
                logger.debug(f"Updated Trakt {self.name}: {result}")
        finally:
            self.items.clear()
            self.last_sent_time = time()

    def queue_size(self):
        size = 0
        for media_type in self.items:
            size += len(self.items[media_type])

        return size

    def flush(self, force=False):
        """
        Flush the queue every batch_delay seconds
        """
        if not self.batch_delay and force is False:
            return
        if self.queue_size() == 0:
            return

        elapsed = time() - self.last_sent_time
        if elapsed >= self.batch_delay or force is True:
            self.submit()

    def add_to_items(self, media_type: str, item):
        """
        Add item of media_type to list of items
        """
        self.items[media_type].append(item)
        self.flush()

    def trakt_sync(self, media_object):
        if self.name == "collection":
            if self.add:
                return trakt.sync.add_to_collection(media_object)
            else:
                return trakt.sync.remove_from_collection(media_object)
        if self.name == "watchlist":
            if self.add:
                return trakt.sync.add_to_watchlist(media_object)
            else:
                return trakt.sync.remove_from_watchlist(media_object)

    @staticmethod
    def remove_empty_values(result):
        """
        Update result to remove empty changes.
        This makes diagnostic printing cleaner if we don't print "changed: 0"
        """
        for change_type in ["added", "existing", "updated"]:
            if change_type in result:
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


EPISODES_ORDERING_WARNING = "episodes ordering is different in Plex and Trakt. " \
                            "Check your Plex media source, TMDB is recommended."


class TraktLookup:
    """
    Trakt lookup table to find all Trakt episodes of a TVShow
    """
    def __init__(self, tm: TVShow):
        self.provider_table = {}
        self.tm = tm
        self.same_order = True

    @cached_property
    @nocache
    @retry()
    def table(self):
        """
        Build a lookup-table accessible via table[season][episode]

        - https://github.com/moogar0880/PyTrakt/pull/185
        """

        seasons = {}
        for season in self.tm.seasons:
            episodes = {}
            for episode in season.episodes:
                episodes[episode.number] = episode
            seasons[season.season] = episodes
        return seasons

    def _reverse_lookup(self, provider):
        """
        Build a lookup-table accessible via table[provider][id]
        only if episodes ordering is different between Plex and Trakt
        """
        # NB: side effect, assumes that from_number() is called first to populate self.table
        table = {}
        for season in self.table.keys():
            for te in self.table[season].values():
                table[str(te.ids.get(provider))] = te
        self.provider_table[provider] = table
        logger.debug(f"{self.tm.title}: lookup table build with '{provider}' ids")

    def from_guid(self, guid: PlexGuid):
        """
        Find Trakt Episode from Guid of Plex Episode
        """
        te = self.from_number(guid.pm.season_number, guid.pm.episode_number)
        if self.invalid_match(guid, te):
            te = self.from_id(guid.provider, guid.id)

        return te

    @staticmethod
    def invalid_match(guid: PlexGuid, episode: Optional[TVEpisode]) -> bool:
        """
        Checks if guid and episode don't match by comparing trakt provided id
        """

        if not episode:
            # nothing to compare with
            return True
        if guid.pm.is_legacy_agent:
            # check can not be performed
            return False
        id_from_trakt = getattr(episode, guid.provider, None)
        if str(id_from_trakt) != guid.id:
            return True
        return False

    def from_number(self, season, number):
        try:
            ep = self.table[season][number]
        except KeyError:
            return None
        return ep

    def from_id(self, provider, id):
        # NB: the code assumes from_id is called only if from_number fails
        if provider not in self.provider_table:
            self._reverse_lookup(provider)
        try:
            ep = self.provider_table[provider][id]
        except KeyError:
            return None
        if self.same_order:
            logger.warning(f"'{self.tm.title}' {EPISODES_ORDERING_WARNING}")
            self.same_order = False
        return ep
