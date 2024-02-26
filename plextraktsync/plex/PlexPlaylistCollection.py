from __future__ import annotations

from collections import UserDict
from typing import TYPE_CHECKING

from plextraktsync.plex.PlexPlaylist import PlexPlaylist

if TYPE_CHECKING:
    from plexapi.library import LibrarySection

    from plextraktsync.plex.PlexApi import PlexApi


class PlexPlaylistCollection(UserDict):
    def __init__(self, plex: PlexApi, section: LibrarySection):
        super().__init__()
        self.plex = plex
        self.section = section

    def __missing__(self, name: str):
        self[name] = playlist = PlexPlaylist(plex=self.plex, section=self.section, name=name)

        return playlist
