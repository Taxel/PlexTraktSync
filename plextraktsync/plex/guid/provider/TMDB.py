from __future__ import annotations

from functools import cached_property

from .Abstract import Abstract


class TMDB(Abstract):
    url = "https://www.themoviedb.org"

    @cached_property
    def link(self):
        url = f"{self.url}/{self.type}"
        type = self.guid.type

        if type in ["show", "season", "episode"]:
            url += f"/{self.show_guid.id}"

        if type in ["season", "episode"]:
            url += f"/season/{self.season_number}"

        if type == "episode":
            url += f"/episode/{self.episode_number}"

        if type == "movie":
            url += f"/{self.guid.id}"

        return url

    @property
    def show_guid(self):
        pm = self.guid.pm
        guids = pm.guids if self.guid.type == "show" else pm.show.guids
        return next(guid for guid in guids if guid.provider == "tmdb")

    @property
    def season_number(self):
        return self.guid.pm.season_number

    @property
    def episode_number(self):
        return self.guid.pm.episode_number

    @property
    def type(self):
        return {
            "show": "tv",
            "season": "tv",
            "episode": "tv",
            "movie": "movie",
        }[self.guid.type]
