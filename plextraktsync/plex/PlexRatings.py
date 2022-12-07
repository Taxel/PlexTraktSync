from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.flatten import flatten_dict
from plextraktsync.decorators.memoize import memoize

if TYPE_CHECKING:
    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem
    from plextraktsync.plex.PlexLibrarySection import PlexLibrarySection


class PlexRatings:
    plex: PlexApi

    def __init__(self, plex: PlexApi):
        self.plex = plex

    def get(self, m: PlexLibraryItem, show_id: int = None):
        section_id = m.item.librarySectionID
        media_type = m.media_type
        section = self.plex.library_sections[section_id]
        ratings = self.ratings(section, media_type)

        if media_type in ["movies", "shows"]:
            # For movies and shows, just return from the dict
            user_rating = (
                ratings[m.item.ratingKey] if m.item.ratingKey in ratings else None
            )
        elif media_type == "episodes":
            # For episodes the ratings is just (show_id, show_rating) tuples
            # if show id is not listed, return none, otherwise fetch from item itself
            if show_id not in ratings:
                return None
            user_rating = m.item.userRating
        else:
            raise RuntimeError(f"Unsupported media type: {media_type}")

        if user_rating is None:
            return None

        return int(user_rating)

    @staticmethod
    @memoize
    @flatten_dict
    def ratings(section: PlexLibrarySection, media_type: str):
        key = {
            "movies": "userRating",
            "episodes": "episode.userRating",
            "shows": "show.userRating",
        }[media_type]

        filters = {
            "and": [
                {f"{key}>>": -1},
            ]
        }

        for item in section.search(filters=filters):
            yield item.ratingKey, item.userRating
