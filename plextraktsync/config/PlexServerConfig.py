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

    def asdict(self):
        data = asdict(self)
        del data["name"]

        return data
