from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.flatten import flatten_dict

from trakt.movies import Movie
from trakt.tv import TVEpisode, TVSeason, TVShow

if TYPE_CHECKING:
    from plextraktsync.trakt.TraktApi import TraktApi

trakt_types = {
    "movie": Movie,
    "show": TVShow,
    "season": TVSeason,
    "episode": TVEpisode,
}


class TraktRatingCollection(dict):
    def __init__(self, trakt: TraktApi):
        super().__init__()
        self.trakt = trakt
        self.items = dict()

    def __missing__(self, media_type: str):
        ratings = self.ratings(media_type)
        self[media_type] = ratings
        self.items[media_type] = self.rating_items(media_type)

        return ratings

    @flatten_dict
    def ratings(self, media_type: str):
        """Yield trakt id and rating of all rated media_type"""
        index = media_type.rstrip("s")
        for r in self.trakt.get_ratings(media_type):
            yield r[index]["ids"]["trakt"], r["rating"]

    def rating_items(self, media_type: str):
        """Yield TraktMedia of all rated media_type"""
        index = media_type.rstrip("s")
        for r in self.trakt.get_ratings(media_type):
            title = r[index].get("title")
            if index == "movie":
                show = season = number = None
            else:
                show = title = r["show"]["title"]
            if index == "episode":
                season = r[index]["season"]
                number = r[index]["number"]
            if index == "season":
                season = r[index]["number"]
                number = None
            ids = r[index]["ids"]
            yield trakt_types[index](
                title=title,
                show=show,
                season=season,
                number=number,
                ids=ids,
            )
