from __future__ import annotations

from functools import cached_property

from .Abstract import Abstract


class Mbid(Abstract):
    @cached_property
    def link(self):
        if self.guid.type == "artist":
            return f"https://musicbrainz.org/artist/{self.guid.id}"
        if self.guid.type == "album":
            return f"https://musicbrainz.org/release/{self.guid.id}"
