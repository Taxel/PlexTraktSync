from __future__ import annotations

from plextraktsync.decorators.flatten import flatten_dict
from plextraktsync.trakt_api import TraktApi


class TraktRatingCollection(dict):
    def __init__(self, trakt: TraktApi):
        super().__init__()
        self.trakt = trakt

    def __missing__(self, media_type: str):
        ratings = self.ratings(media_type)
        self[media_type] = ratings

        return ratings

    @flatten_dict
    def ratings(self, media_type: str):
        index = media_type.rstrip("s")
        for r in self.trakt.get_ratings(media_type):
            yield r[index]["ids"]["trakt"], r["rating"]
