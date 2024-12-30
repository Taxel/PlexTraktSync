from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plextraktsync.plex.PlexGuid import PlexGuid


class PlexGuidProviderYoutube:
    def __init__(self, guid: PlexGuid):
        self.guid = guid

    @property
    def id(self):
        return self.guid.id.split("|")[1]

    @property
    def link(self):
        return f"https://www.youtube.com/watch?v={self.id}"

    @property
    def title(self):
        return f"{self.guid.provider}:{self.guid.type}:{self.guid.id}"
