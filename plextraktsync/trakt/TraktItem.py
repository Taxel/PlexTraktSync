from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.cached_property import cached_property

if TYPE_CHECKING:
    from plextraktsync.trakt.TraktApi import TraktApi
    from plextraktsync.trakt.types import TraktMedia


class TraktItem:
    def __init__(self, item: TraktMedia, trakt: TraktApi = None):
        self.item = item
        self.trakt = trakt

    @cached_property
    def type(self):
        """
        Return "movie", "show", "season", "episode"
        """
        # NB: TVSeason does not have "media_type" property
        return self.item.media_type[:-1]
