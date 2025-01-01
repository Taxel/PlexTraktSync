from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.rich.RichMarkup import RichMarkup

if TYPE_CHECKING:
    from plextraktsync.plex.guid.PlexGuid import PlexGuid


class Abstract(RichMarkup):
    def __init__(self, guid: PlexGuid):
        self.guid = guid

    @cached_property
    def title(self):
        return f"{self.guid.provider}:{self.guid.type}:{self.guid.id}"

    @cached_property
    def link(self) -> str | None:
        return None

    @cached_property
    def markup(self):
        if not self.link:
            return self.markup_title(self.title)

        return self.markup_link(self.link, self.title)
