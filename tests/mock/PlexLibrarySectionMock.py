from __future__ import annotations

from plextraktsync.plex.PlexLibrarySection import PlexLibrarySection


class PlexLibrarySectionMock(PlexLibrarySection):
    def __init__(self, data):
        self.data = data

    @property
    def title(self):
        return self.data["title"]

    def find_by_title(self, name: str):
        items = [item for item in self.data["items"] if item["title"] == name]
        assert len(items) == 1
        return items[0]
