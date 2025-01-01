from __future__ import annotations

from typing import TYPE_CHECKING

from .IMDB import IMDB
from .Local import Local
from .Mbid import Mbid
from .TMDB import TMDB
from .TVDB import TVDB
from .Youtube import Youtube

if TYPE_CHECKING:
    from plextraktsync.plex.guid.PlexGuid import PlexGuid


class Factory:
    @classmethod
    def create(cls, guid: PlexGuid):
        if guid.provider == "imdb":
            return IMDB(guid)
        if guid.provider == "tmdb":
            return TMDB(guid)
        if guid.provider == "tvdb":
            return TVDB(guid)
        if guid.provider == "mbid":
            return Mbid(guid)
        if guid.provider == "youtube":
            return Youtube(guid)
        if guid.provider in ["local", "none"]:
            return Local(guid)

        raise RuntimeError(f"Unsupported provider: {guid.provider}")
