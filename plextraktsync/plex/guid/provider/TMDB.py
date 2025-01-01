from __future__ import annotations

from functools import cached_property

from .Abstract import Abstract


class TMDB(Abstract):
    url = "https://www.themoviedb.org"

    @cached_property
    def link(self):
        if self.guid.type == "episode":
            return f"{self.url}/tv/{self.show_guid.id}/season/{self.season_number}/episode/{self.episode_number}"

        return f"{self.url}/{self.type}/{self.guid.id}"

    @property
    def show_guid(self):
        return next(guid for guid in self.guid.pm.show.guids if guid.provider == "tmdb")

    @property
    def season_number(self):
        return self.guid.pm.season_number

    @property
    def episode_number(self):
        return self.guid.pm.episode_number

    @property
    def type(self):
        try:
            return {
                "show": "tv",
                "movie": "movie",
            }[self.guid.type]
        except IndexError:
            return ""
