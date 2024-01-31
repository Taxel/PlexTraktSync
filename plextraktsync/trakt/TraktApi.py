from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

import trakt
import trakt.movies
import trakt.sync
import trakt.users
from click import ClickException
from trakt.errors import (ForbiddenException, OAuthException,
                          OAuthRefreshException)

from plextraktsync import pytrakt_extensions
from plextraktsync.decorators.flatten import flatten_list
from plextraktsync.decorators.rate_limit import rate_limit
from plextraktsync.decorators.retry import retry
from plextraktsync.decorators.time_limit import time_limit
from plextraktsync.factory import factory, logger
from plextraktsync.path import pytrakt_file
from plextraktsync.trakt.PartialTraktMedia import PartialTraktMedia
from plextraktsync.trakt.TraktLookup import TraktLookup
from plextraktsync.trakt.TraktRatingCollection import TraktRatingCollection

if TYPE_CHECKING:
    from trakt.movies import Movie
    from trakt.tv import TVEpisode, TVShow

    from plextraktsync.plex.PlexGuid import PlexGuid
    from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem
    from plextraktsync.trakt.types import TraktLikedList, TraktMedia


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
    @rate_limit()
    @retry()
    def me(self):
        try:
            return trakt.users.User("me")
        except OAuthRefreshException as e:
            logger.error(f"{e.error}: {e.error_description}")
            raise ClickException("Trakt error: Unable to refresh token")
        except (OAuthException, ForbiddenException) as e:
            raise ClickException(f"Trakt authentication error: {str(e)}")

    @cached_property
    @rate_limit()
    @retry()
    @flatten_list
    def liked_lists(self) -> list[TraktLikedList]:
        for item in self.me.get_liked_lists("lists", limit=1000):
            tll: TraktLikedList = {
                'listname': item['list']['name'],
                'listid': item['list']['ids']['trakt'],
            }
            yield tll

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

    @property
    @rate_limit()
    @retry()
    def show_collection(self):
        return self.me.show_collection

    @cached_property
    @flatten_list
    def episodes_collection(self) -> list[TVEpisode]:
        for show in self.show_collection:
            for season in show.seasons:
                yield from season.episodes

    def remove_from_collection(self, m: TraktMedia):
        if m.media_type not in ["movies", "shows", "episodes"]:
            raise ValueError(f"Unsupported media type: {m.media_type}")

        item = dict(
            title=m.title,
            year=m.year,
            **m.ids,
        )

        self.queue.remove_from_collection((m.media_type, item))

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

    @property
    @rate_limit()
    @retry()
    def watchlist_movies(self):
        return self.me.watchlist_movies

    @property
    @rate_limit()
    @retry()
    def watchlist_shows(self):
        return self.me.watchlist_shows

    @cached_property
    def ratings(self):
        return TraktRatingCollection(self)

    def rating(self, m) -> int | None:
        """
        The trakt api (Python module) is inconsistent:
        - Movie has "rating" property, while TVShow does not
        However, the Movie property is always None.
        So fetch for all types.
        """
        if m.media_type not in ["movies", "shows", "episodes"]:
            raise ValueError(f"Unsupported type: {m.media_type}")

        return self.ratings[m.media_type].get(m.trakt, None)

    @rate_limit()
    @retry()
    def get_ratings(self, media_type: str):
        return self.me.get_ratings(media_type)

    @rate_limit()
    @time_limit()
    @retry()
    def rate(self, m, rating):
        m.rate(rating)

    @rate_limit()
    @time_limit()
    @retry()
    def mark_watched(self, m: TraktMedia, time, show_trakt_id=None):
        if m.media_type == "movies":
            self.watched_movies.add(m.trakt)
        elif m.media_type == "episodes" and show_trakt_id:
            self.watched_shows.add(show_trakt_id, m.season, m.number)
        else:
            raise RuntimeError(f"mark_watched: Unsupported media type: {m.media_type}")

        # Add partial object to conserve memory
        partial = PartialTraktMedia.create(m, watched_at=time)
        self.queue.add_to_history(partial)

    def add_to_collection(self, m, pm: PlexLibraryItem):
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

        self.queue.add_to_collection((m.media_type, item))

    def add_to_watchlist(self, m):
        if m.media_type not in ["movies", "shows"]:
            raise ValueError(f"Unsupported media type for watchlist: {m.media_type}")

        item = dict(
            title=m.title,
            year=m.year,
            **m.ids,
        )

        self.queue.add_to_watchlist((m.media_type, item))

    def remove_from_watchlist(self, m):
        if m.media_type not in ["movies", "shows"]:
            raise ValueError(f"Unsupported media type for watchlist: {m.media_type}")

        item = dict(
            title=m.title,
            year=m.year,
            **m.ids,
        )

        self.queue.remove_from_watchlist((m.media_type, item))

    def find_by_episode_guid(self, guid: PlexGuid):
        ts: TVShow = self.search_by_id(guid.show_id, id_type=guid.provider, media_type="show")
        if not ts:
            return None

        lookup = TraktLookup(ts)
        te = self.find_episode_guid(guid, lookup)
        if not te:
            return None

        # NOTE: overwrites property of type str
        te.show = ts

        return te

    def find_by_guid(self, guid: PlexGuid):
        if guid.type == "episode" and guid.is_episode:
            return self.find_by_episode_guid(guid)
        else:
            tm = self.search_by_id(guid.id, id_type=guid.provider, media_type=guid.type)
            if tm is None and guid.type == "movie":
                if self.search_by_id(guid.id, id_type=guid.provider, media_type="show"):
                    logger.warning(f"Found match using show search: {guid.title_link}", extra={"markup": True})

            return tm

    @rate_limit()
    @retry()
    def search_by_id(self, media_id: str, id_type: str, media_type: str) -> TVShow | Movie | None:
        if id_type == "tvdb" and media_type == "movie":
            # Skip invalid search.
            # The Trakt API states that tvdb is only for shows and episodes:
            # https://trakt.docs.apiary.io/#reference/search/id-lookup/get-id-lookup-results
            logger.debug(f"search_by_id: tvdb does not support movie provider, skip {id_type}/{media_type}/{media_id}")
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
        if not search:
            return None

        if len(search) > 1:
            logger.debug(f"search_by_id({media_id}, {id_type}, {media_type}) got {len(search)} results, taking first one")
            logger.debug([pm.to_json() for pm in search])

        # TODO: sort by "score"?
        return search[0]

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

    @cached_property
    def queue(self):
        return factory.queue
