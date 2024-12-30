from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plextraktsync.plex.PlexGuid import PlexGuid


class PlexGuidProviderMbid:
    def __init__(self, guid: PlexGuid):
        self.guid = guid

    @property
    def link(self):
        if self.guid.type == "artist":
            return f"https://musicbrainz.org/artist/{self.guid.id}"
        if self.guid.type == "album":
            return f"https://musicbrainz.org/release/{self.guid.id}"

    @property
    def title(self):
        return f"{self.guid.provider}:{self.guid.type}:{self.guid.id}"
