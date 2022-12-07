from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.factory import factory

if TYPE_CHECKING:
    from typing import Optional

    from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem


class PlexGuid:
    def __init__(self, guid: str, type: str, pm: Optional[PlexLibraryItem] = None):
        self.guid = guid
        self.type = type
        self.pm = pm

    @cached_property
    def media_type(self):
        return f"{self.type}s"

    @cached_property
    def provider(self):
        if self.guid_is_imdb_legacy:
            return "imdb"
        x = self.guid.split("://")[0]
        x = x.replace("com.plexapp.agents.", "")
        x = x.replace("tv.plex.agents.", "")
        x = x.replace("themoviedb", "tmdb")
        x = x.replace("thetvdb", "tvdb")
        if x == "xbmcnfo":
            CONFIG = factory.config
            x = CONFIG["xbmc-providers"][self.media_type]
        if x == "xbmcnfotv":
            CONFIG = factory.config
            x = CONFIG["xbmc-providers"]["shows"]

        return x

    @cached_property
    def id(self):
        if self.guid_is_imdb_legacy:
            return self.guid
        x = self.guid.split("://")[1]
        x = x.split("?")[0]
        return x

    @cached_property
    def is_episode(self):
        """
        Return true of the id is in form of <show>/<season>/<episode>
        """
        parts = self.id.split("/")
        if len(parts) == 3 and all(x.isnumeric() for x in parts):
            return True

        return False

    @cached_property
    def show_id(self):
        if not self.is_episode:
            raise ValueError("show_id is not valid for non-episodes")

        show = self.id.split("/", 1)[0]
        if not show.isnumeric():
            raise ValueError(f"show_id is not numeric: {show}")

        return show

    @cached_property
    def guid_is_imdb_legacy(self):
        guid = self.guid

        # old item, like imdb 'tt0112253'
        return guid[0:2] == "tt" and guid[2:].isnumeric()

    def __str__(self):
        return f"<PlexGuid:{self.guid}>"
