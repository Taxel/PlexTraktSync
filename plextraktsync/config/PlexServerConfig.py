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

        return data

    @property
    def sync_config(self):
        if self.config is None or "sync" not in self.config or self.config["sync"] is None:
            return {}

        return self.config["sync"]
