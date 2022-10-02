from dataclasses import dataclass
from typing import List


@dataclass
class PlexServerConfig:
    """
    Class to hold single server config
    """

    name: str = ""
    token: str = ""
    urls: List[str] = None
