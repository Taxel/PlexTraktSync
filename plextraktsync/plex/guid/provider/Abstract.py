from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plextraktsync.plex.guid.PlexGuid import PlexGuid


class Abstract:
    def __init__(self, guid: PlexGuid):
        self.guid = guid
