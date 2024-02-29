from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.decorators.flatten import flatten_set

if TYPE_CHECKING:
    from plextraktsync.media.Media import Media
    from plextraktsync.plex.types import PlexMedia


class PlexWatchList:
    def __init__(self, watchlist: list[PlexMedia]):
        if watchlist is None:
            raise RuntimeError("Plex watchlist is None")
        self.watchlist = watchlist

    def __iter__(self):
        return iter(self.watchlist)

    def __len__(self):
        return len(self.watchlist)

    def __contains__(self, m: Media):
        return m.plex.item.guid in self.guidmap

    @cached_property
    @flatten_set
    def guidmap(self) -> set[str]:
        """
        Return set() of guid of Plex Watchlist items
        """
        for pm in self.watchlist:
            yield pm.guid
