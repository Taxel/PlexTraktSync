from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.decorators.retry import retry
from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem

if TYPE_CHECKING:
    from plexapi.library import MovieSection, ShowSection

    from plextraktsync.plex.PlexApi import PlexApi


class PlexSectionPager:
    def __init__(
        self, section: ShowSection | MovieSection, plex: PlexApi, libtype: str = None
    ):
        self.section = section
        self.plex = plex
        self.libtype = libtype if libtype is not None else section.TYPE

    def __len__(self):
        return self.total_size

    @cached_property
    def total_size(self):
        return self.section.totalViewSize(
            libtype=self.libtype, includeCollections=False
        )

    @retry()
    def fetch_items(self, start: int, size: int):
        return self.section.search(
            libtype=self.libtype,
            container_start=start,
            container_size=size,
            maxresults=size,
        )

    def __iter__(self):
        from plexapi import X_PLEX_CONTAINER_SIZE

        max_items = self.total_size
        start = 0
        size = X_PLEX_CONTAINER_SIZE

        while True:
            items = self.fetch_items(start=start, size=size)

            if not len(items):
                break

            for ep in items:
                yield PlexLibraryItem(ep, plex=self.plex)

            start += size
            if start > max_items:
                break
