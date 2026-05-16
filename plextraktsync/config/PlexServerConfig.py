from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class PlexServerConfig:
    """
    Class to hold single server config
    """

    name: str
    token: str
    urls: list[str]
    # The machineIdentifier value of this server
    id: str = None
    config: dict = None

    def asdict(self):
        data = asdict(self)
        del data["name"]

        # Remove optional fields that are None so they don't overwrite
        # existing values when merging (e.g. preserving user config on re-login)
        for key in ("id", "config"):
            if data[key] is None:
                del data[key]

        return data

    @property
    def sync_config(self):
        return self.get_section("sync", {})

    @property
    def libraries(self):
        return self.get_section("libraries")

    @property
    def excluded_libraries(self):
        return self.get_section("excluded-libraries")

    def get_section(self, section: str, default=None):
        if self.config is None:
            return default

        return self.config.get(section, default)
