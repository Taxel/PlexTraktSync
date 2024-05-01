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

    def __init__(self, keep_watched: bool, trakt_lists_overrides: dict):
        super().__init__()
        self.keep_watched = keep_watched
        self.trakt_lists_overrides = trakt_lists_overrides

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
        list_config = self.trakt_lists_overrides.get(list_name, {})
        keep_watched = list_config.get("keep_watched", self.keep_watched)
        tl = TraktUserList.from_trakt_list(list_id, list_name, keep_watched)
        self.append(tl)
        return tl
