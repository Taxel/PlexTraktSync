from __future__ import annotations

from collections import UserDict
from typing import TYPE_CHECKING

from plextraktsync.plex.PlexPlaylist import PlexPlaylist

if TYPE_CHECKING:
    from plexapi.library import LibrarySection


class PlexPlaylistCollection(UserDict):
    def __init__(self, section: LibrarySection):
        super().__init__()
        self.section = section

    def __missing__(self, name: str):
        self[name] = playlist = PlexPlaylist(self.section, name)

        return playlist
