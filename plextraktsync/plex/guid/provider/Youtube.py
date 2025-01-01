from __future__ import annotations

from functools import cached_property

from .Abstract import Abstract


class Youtube(Abstract):
    @property
    def id(self):
        return self.guid.id.split("|")[1]

    @cached_property
    def link(self):
        return f"https://www.youtube.com/watch?v={self.id}"

    @cached_property
    def title(self):
        return f"{self.guid.provider}:{self.guid.type}:{self.id}"
