from __future__ import annotations

from functools import cached_property

from .Abstract import Abstract


class TVDB(Abstract):
    @cached_property
    def link(self):
        return f"https://www.thetvdb.com/dereferrer/{self.guid.type}/{self.guid.id}"
