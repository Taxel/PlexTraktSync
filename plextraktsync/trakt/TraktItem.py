from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.mixin.RichMarkup import RichMarkup

if TYPE_CHECKING:
    from plextraktsync.trakt.types import TraktMedia


class TraktItem(RichMarkup):
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

    @property
    def title_link(self):
        link = f"https://trakt.tv/{self.item.ext}"

        return self.markup_link(link, self.item.title)
