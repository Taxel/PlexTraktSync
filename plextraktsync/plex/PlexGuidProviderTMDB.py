from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plextraktsync.plex.PlexGuid import PlexGuid


class PlexGuidProviderTMDB:
    def __init__(self, guid: PlexGuid):
        self.guid = guid

    @property
    def link(self):
        return f"https://www.themoviedb.org/{self.type}/{self.guid.id}"

    @property
    def title(self):
        return f"{self.guid.provider}:{self.guid.type}:{self.guid.id}"

    @property
    def type(self):
        try:
            return {
                "show": "tv",
                "movie": "movie",
            }[self.guid.type]
        except IndexError:
            return ""
