from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plextraktsync.trakt.types import TraktMedia


class TraktItem:
    def __init__(self, item: TraktMedia):
        self.item = item

    @cached_property
    def type(self):
        """
        Return "movie", "show", "season", "episode"
        """
        # NB: TVSeason does not have "media_type" property
        return self.item.media_type[:-1]

    @property
    def guids(self):
        return {k: v for k, v in self.item.ids["ids"].items() if k in ["imdb", "tmdb", "tvdb"]}
