from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.flatten import flatten_dict

if TYPE_CHECKING:
    from plextraktsync.trakt.TraktApi import TraktApi


class TraktRatingCollection(dict):
    """
    A dictionary of:
    ["movies", "shows", "episodes"] => {
        trakt_id => rating
    }
    """
    def __init__(self, trakt: TraktApi):
        super().__init__()
        self.trakt = trakt

    def __missing__(self, media_type: str):
        self[media_type] = ratings = self.ratings(media_type)

        return ratings

    @flatten_dict
    def ratings(self, media_type: str):
        index = media_type.rstrip("s")
        for r in self.trakt.get_ratings(media_type):
            yield r[index]["ids"]["trakt"], r["rating"]
