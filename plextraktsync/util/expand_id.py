from __future__ import annotations

from plextraktsync.plex.PlexIdFactory import PlexIdFactory


def expand_plexid(input):
    for id in input:
        yield PlexIdFactory.create(id)
