from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.factory import factory
from plextraktsync.rich.RichMarkup import RichMarkup

from .provider.Factory import Factory as GuidProviderFactory

if TYPE_CHECKING:
    from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem


class PlexGuid(RichMarkup):
    def __init__(self, guid: str, type: str, pm: PlexLibraryItem | None = None):
        self.guid = guid
        self.type = type
        self.pm = pm

    @cached_property
    def media_type(self):
        return f"{self.type}s"

    def __eq__(self, other: PlexGuid):
        # These are same guids even they come from different Agent
        # compare <PlexGuid:imdb://tt0100802> with <PlexGuid:com.plexapp.agents.imdb://tt0100802?lang=en>
        return self.provider == other.provider and self.id == other.id

    @cached_property
    def provider(self):
        if self.guid_is_imdb_legacy:
            return "imdb"
        x = self.guid.split("://")[0]
        x = x.replace("com.plexapp.agents.", "")
        x = x.replace("tv.plex.xmltv", "xmltv")
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

        return len(parts) == 3 and all(x.isnumeric() for x in parts)

    @property
    def syncable(self):
        """Is the provider syncable with trakt"""
        return self.provider in ["imdb", "tmdb", "tvdb"]

    @property
    def local(self):
        """Is the provider local"""
        return self.provider in ["local", "none", "agents.none"]

    @property
    def unsupported(self):
        """Known providers that can't be synced"""
        return self.provider in ["youtube", "xmltv"]

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

    @property
    def title(self):
        return self.pm.item.title

    @property
    def title_link(self):
        if self.pm:
            return self.pm.title_link

        return self.markup_title(str(self))

    @property
    def provider_link(self):
        provider = GuidProviderFactory().create(self)
        link = provider.link

        if not link:
            return self.markup_title(provider.title)

        return self.markup_link(link, provider.title)

    def __str__(self):
        return f"<PlexGuid:{self.guid}>"
