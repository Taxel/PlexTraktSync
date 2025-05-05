from __future__ import annotations

from typing import TypedDict, Union

from trakt.movies import Movie
from trakt.tv import TVEpisode, TVSeason, TVShow

TraktMedia = Union[Movie, TVShow, TVSeason, TVEpisode]
TraktPlayable = Union[Movie, TVEpisode]


class TraktLikedList(TypedDict):
    listid: int
    listname: str
    private: bool
    list_type: str  # 'personal' or 'official'
