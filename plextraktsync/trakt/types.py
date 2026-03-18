from __future__ import annotations

from typing import TypedDict

from trakt.movies import Movie
from trakt.tv import TVEpisode, TVSeason, TVShow

TraktMedia = Movie | TVShow | TVSeason | TVEpisode
TraktPlayable = Movie | TVEpisode


class TraktLikedList(TypedDict):
    listid: int
    listname: str
    username: str
    private: bool
    list_type: str  # 'personal' or 'official'
