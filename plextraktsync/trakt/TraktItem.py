from __future__ import annotations

from typing import Union

from trakt.movies import Movie
from trakt.tv import TVEpisode, TVSeason, TVShow

from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.trakt_api import TraktApi


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
