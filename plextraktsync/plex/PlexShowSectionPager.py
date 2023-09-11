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
        maxresults = self.section.searchEpisodes(maxresults=0)
        try:
            return maxresults.total_size
        except AttributeError:
            raise RuntimeError("Needs PlexAPI patch")

    def __iter__(self):
        for ep in self.section.searchEpisodes():
            yield PlexLibraryItem(ep, plex=self.plex)
