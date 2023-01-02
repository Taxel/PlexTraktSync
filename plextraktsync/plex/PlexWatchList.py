from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.decorators.flatten import flatten_set

if TYPE_CHECKING:
    from typing import List, Set

    from plextraktsync.media import Media
    from plextraktsync.plex.types import PlexMedia


class PlexWatchList:
    def __init__(self, watchlist: List[PlexMedia]):
        self.watchlist = watchlist

    def __iter__(self):
        return iter(self.watchlist)

    def __len__(self):
        return len(self.watchlist)

    def __contains__(self, m: Media):
        return m.plex.item.guid in self.guidmap

    @cached_property
    @flatten_set
    def guidmap(self) -> Set[str]:
        """
        Return set() of guid of Plex Watchlist items
        """
        for pm in self.watchlist:
            yield pm.guid
