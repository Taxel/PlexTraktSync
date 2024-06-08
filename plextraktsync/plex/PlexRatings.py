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
        if m.media_type not in ["movies", "shows", "episodes"]:
            raise RuntimeError(f"Unsupported media type: {m.media_type}")

        section = self.plex.library_sections[section_id]
        ratings: dict[int, Rating] = self.ratings(section, m.media_type)

        return ratings.get(m.item.ratingKey, None)

    @staticmethod
    @memoize
    @flatten_dict
    def ratings(section: PlexLibrarySection, media_type: str):
        key = {
            "movies": "userRating",
            "episodes": "episode.userRating",
            "shows": "show.userRating",
        }[media_type]
        libtype = {
            "movies": "movie",
            "episodes": "episode",
            "shows": "show",
        }[media_type]

        filters = {
            "and": [
                {f"{key}>>": -1},
            ]
        }

        for item in section.search(
            filters=filters, libtype=libtype, includeGuids=False
        ):
            yield item.ratingKey, Rating.create(item.userRating, item.lastRatedAt)
