from __future__ import annotations

from functools import cached_property

from .Abstract import Abstract


class IMDB(Abstract):
    @cached_property
    def link(self):
        return f"https://www.imdb.com/title/{self.guid.id}/"
