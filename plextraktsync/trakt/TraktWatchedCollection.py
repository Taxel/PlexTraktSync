from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.flatten import flatten_dict

if TYPE_CHECKING:
    from plextraktsync.trakt.TraktApi import TraktApi


class TraktWatchedCollection(dict):
    """
    A dictionary of:
    ["movies", "episodes"] => {
        trakt_id => TraktItem
    }
    """

    def __init__(self, trakt: TraktApi):
        super().__init__()
        self.trakt = trakt

    def __missing__(self, media_type: str):
        self[media_type] = items = self.watched_items(media_type)

        return items

    @flatten_dict
    def watched_items(self, media_type: str):
        if media_type == "movies":
            for movie in self.trakt.me.watched_movies:
                yield movie.trakt, movie
        elif media_type == "episodes":
            for episode in self.trakt.me.watched_episodes:
                yield episode.trakt, episode
        else:
            raise ValueError(f"Unsupported media type: {media_type}")
