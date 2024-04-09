from __future__ import annotations

from collections import UserList
from typing import TYPE_CHECKING

from plextraktsync.factory import logging
from plextraktsync.trakt.TraktUserList import TraktUserList

if TYPE_CHECKING:
    from plextraktsync.media.Media import Media
    from plextraktsync.trakt.types import TraktLikedList, TraktPlayable


class TraktUserListCollection(UserList):
    logger = logging.getLogger(__name__)

    @property
    def is_empty(self):
        return not len(self)

    def add_to_lists(self, m: Media):
        # Skip movie editions
        # https://support.plex.tv/articles/multiple-editions/#:~:text=Do%20Multiple%20Editions%20work%20with%20watch%20state%20syncing%3F
        if m.plex.edition_title is not None:
            return
        for tl in self:
            tl.add(m)

    def load_lists(self, liked_lists: list[TraktLikedList]):
        for liked_list in liked_lists:
            self.add_list(liked_list["listid"], liked_list["listname"])

    def add_watchlist(self, items: list[TraktPlayable]):
        tl = TraktUserList.from_watchlist(items)
        self.append(tl)
        return tl

    def add_list(self, list_id: int, list_name: str):
        tl = TraktUserList.from_trakt_list(list_id, list_name)
        self.append(tl)
        return tl

    def sync(self):
        for tl in self:
            updated = tl.plex_list.update(tl.plex_items_sorted)
            if not updated:
                continue
            self.logger.info(f"Plex list {tl.title_link} ({len(tl.plex_items)} items) updated", extra={"markup": True})
