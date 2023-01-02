from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.decorators.flatten import flatten_dict

if TYPE_CHECKING:
    from typing import Dict, List

    from plextraktsync.media import Media
    from plextraktsync.trakt.types import TraktMedia


class TraktWatchList:
    def __init__(self, watchlist: List[TraktMedia]):
        self.watchlist = watchlist

    def __iter__(self):
        return iter(self.watchlist)

    def __len__(self):
        return len(self.watchlist)

    def __contains__(self, m: Media):
        return m.trakt_id in self.idmap

    def __delitem__(self, m: Media):
        for i in (i for i, tm in enumerate(self.watchlist) if tm.trakt == m.trakt_id):
            del self.watchlist[i]

        del self.idmap[m.trakt_id]

    @cached_property
    @flatten_dict
    def idmap(self) -> Dict[int]:
        """
        Return map of trakt_id of Trakt Watchlist items.
        We use dict() rather set() to be able to remove items from it.
        """
        for tm in self.watchlist:
            yield tm.trakt, None
