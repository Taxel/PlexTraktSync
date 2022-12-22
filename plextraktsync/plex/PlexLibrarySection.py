from __future__ import annotations

from typing import TYPE_CHECKING

from plexapi import X_PLEX_CONTAINER_SIZE
from plexapi.exceptions import NotFound

from plextraktsync.decorators.retry import retry
from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem

if TYPE_CHECKING:
    from typing import Optional, Union

    from plexapi.library import LibrarySection

    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.plex.types import PlexMedia


class PlexLibrarySection:
    def __init__(self, section: LibrarySection, plex: PlexApi = None):
        self.section = section
        self.plex = plex

    def __len__(self):
        return self.section.totalSize

    def __iter__(self):
        return self.items(len(self))

    @property
    def type(self):
        return self.section.type

    @property
    def title(self):
        return self.section.title

    def find_by_title(self, name: str):
        try:
            return self.section.get(name)
        except NotFound:
            return None

    def search(self, **kwargs):
        return self.section.search(**kwargs)

    def find_by_id(self, id: Union[str, int]) -> Optional[PlexMedia]:
        try:
            return self.section.fetchItem(int(id))
        except NotFound:
            return None

    def all(self, max_items: int):
        libtype = self.section.TYPE
        key = self.section._buildSearchKey(libtype=libtype, returnKwargs=False)
        start = 0
        size = X_PLEX_CONTAINER_SIZE

        while True:
            items = self.fetch_items(key, size, start)
            if not len(items):
                break

            yield from items

            start += size
            if start > max_items:
                break

    @retry()
    def fetch_items(self, key: str, size: int, start: int):
        return self.section.fetchItems(key, container_start=start, container_size=size)

    def items(self, max_items: int):
        for item in self.all(max_items):
            yield PlexLibraryItem(item, plex=self.plex)

    def __repr__(self):
        return f"<{self.__class__.__name__}:{self.type}:{self.title}>"
