from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plextraktsync.plex.guid.PlexGuid import PlexGuid


class Abstract:
    def __init__(self, guid: PlexGuid):
        self.guid = guid

    @cached_property
    def title(self):
        return f"{self.guid.provider}:{self.guid.type}:{self.guid.id}"
