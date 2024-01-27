from __future__ import annotations

from collections import UserDict
from typing import TYPE_CHECKING

from plextraktsync.plex.PlexPlaylist import PlexPlaylist

if TYPE_CHECKING:
    from plexapi.server import PlexServer


class PlexPlaylistCollection(UserDict):
    def __init__(self, server: PlexServer):
        super().__init__()
        self.server = server

    def __missing__(self, name: str):
        self[name] = playlist = PlexPlaylist(self.server, name)

        return playlist
