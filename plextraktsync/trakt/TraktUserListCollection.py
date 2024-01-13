from __future__ import annotations

from collections import UserList
from typing import TYPE_CHECKING

from plextraktsync.factory import logging
from plextraktsync.trakt.TraktUserList import TraktUserList

if TYPE_CHECKING:
    from trakt.movies import Movie
    from trakt.tv import TVEpisode

    from plextraktsync.media import Media
    from plextraktsync.trakt.types import TraktLikedList


class TraktUserListCollection(UserList):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("PlexTraktSync.TraktUserListCollection")

    def add_to_lists(self, m: Media):
        for tl in self:
            tl.add(m)

    def load_lists(self, liked_lists: list[TraktLikedList]):
        for liked_list in liked_lists:
            self.add_list(liked_list["listid"], liked_list["listname"])

    def add_watchlist(self, items: list[Movie, TVEpisode]):
        tl = TraktUserList.from_watchlist(items)
        self.append(tl)
        return tl

    def add_list(self, list_id: int, list_name: str):
        tl = TraktUserList(list_id, list_name)
        self.append(tl)
        return tl

    def sync(self):
        for tl in self:
            updated = tl.plex_list.update(tl.plex_items_sorted)
            if not updated:
                continue
            self.logger.info(f"Plex list {tl.title_link} ({len(tl.plex_items)} items) updated", extra={"markup": True})
