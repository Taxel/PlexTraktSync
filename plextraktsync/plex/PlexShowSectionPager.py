from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem

if TYPE_CHECKING:
    from plexapi.library import ShowSection

    from plextraktsync.plex.PlexApi import PlexApi


class PlexShowSectionPager:
    def __init__(self, section: ShowSection, plex: PlexApi):
        self.section = section
        self.plex = plex

    def __len__(self):
        return self.total_size

    @cached_property
    def total_size(self):
        return self.section.totalViewSize(libtype="episode", includeCollections=False)

    def __iter__(self):
        from plexapi import X_PLEX_CONTAINER_SIZE

        max_items = self.total_size
        start = 0
        size = X_PLEX_CONTAINER_SIZE

        while True:
            items = self.section.searchEpisodes(container_start=start, container_size=size, maxresults=size)

            if not len(items):
                break

            for ep in items:
                yield PlexLibraryItem(ep, plex=self.plex)

            start += size
            if start > max_items:
                break
