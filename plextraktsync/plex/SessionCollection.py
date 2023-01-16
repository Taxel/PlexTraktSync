from __future__ import annotations

from collections import UserDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from plextraktsync.plex.PlexApi import PlexApi


class SessionCollection(UserDict):
    def __init__(self, plex: PlexApi):
        super().__init__()
        self.plex = plex

    def __missing__(self, key: str):
        self.update_sessions()
        if key not in self:
            # Session probably ended
            return None

        return self[key]

    def update_sessions(self):
        self.clear()
        for session in self.plex.sessions:
            self[str(session.sessionKey)] = session.usernames[0]
