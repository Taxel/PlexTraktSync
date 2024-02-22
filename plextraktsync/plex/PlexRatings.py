from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.flatten import flatten_dict
from plextraktsync.decorators.memoize import memoize
from plextraktsync.util.Rating import Rating

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

        # item is from section that is in excluded-libraries
        # this can happen when doing "inspect"
        if section_id not in self.plex.library_sections:
            return None

        media_type = m.media_type
        section = self.plex.library_sections[section_id]
        ratings: dict[int, Rating] = self.ratings(section, media_type)

        if media_type in ["movies", "shows"]:
            # For movies and shows, just return from the dict
            if m.item.ratingKey in ratings:
                return ratings[m.item.ratingKey]
        elif media_type == "episodes":
            # For episodes the ratings is just (show_id, show_rating) tuples
            # if show id is not listed, return none, otherwise fetch from item itself
            if show_id not in ratings:
                return None
            return Rating.create(m.item.userRating, m.item.lastRatedAt)
        else:
            raise RuntimeError(f"Unsupported media type: {media_type}")

        return None

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

        for item in section.search(filters=filters, includeGuids=False):
            yield item.ratingKey, Rating.create(item.userRating, item.lastRatedAt)
