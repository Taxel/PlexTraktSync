from __future__ import annotations

from typing import TYPE_CHECKING

from plexapi.exceptions import PlexApiException
from requests import RequestException
from trakt.errors import TraktException

from plextraktsync.factory import logging
from plextraktsync.media.Media import Media

if TYPE_CHECKING:
    from plextraktsync.plex.guid.PlexGuid import PlexGuid
    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem
    from plextraktsync.trakt.TraktApi import TraktApi
    from plextraktsync.trakt.TraktItem import TraktItem


class MediaFactory:
    """
    Class that is able to resolve Trakt media item from Plex media item and vice versa and return generic Media class
    """

    logger = logging.getLogger(__name__)

    def __init__(self, plex: PlexApi, trakt: TraktApi):
        self.plex = plex
        self.trakt = trakt

    def resolve_any(self, pm: PlexLibraryItem, show: Media = None) -> Media | None:
        try:
            guids = pm.guids
        except (PlexApiException, RequestException) as e:
            self.logger.error(f"Skipping {pm}: {e}")
            return None

        for guid in guids:
            m = self.resolve_guid(guid, show)
            if m:
                self.logger.debug(f"Resolved {guid} of {guid.pm} to {m}")
                return m

        return None

    def resolve_guid(self, guid: PlexGuid, show: Media = None):
        if not guid.syncable:
            error = f"{guid.title_link}: Skipping {guid} because"

            if guid.unsupported:
                level = "debug"
                reason = f"unsupported provider '{guid.provider}'"
            elif guid.local:
                level = "warning"
                reason = f"provider '{guid.provider}' has no external Id"
            else:
                level = "error"
                reason = "is not a valid provider"

            getattr(self.logger, level)(f"{error} {reason}", extra={"markup": True})

            return None

        try:
            if show:
                tm = self.trakt.find_episode_guid(guid, show.seasons)
            else:
                tm = self.trakt.find_by_guid(guid)
        except (TraktException, RequestException) as e:
            self.logger.warning(
                f"{guid.title_link}: Skipping {guid}: Trakt errors: {e}",
                extra={"markup": True},
            )
            return None

        if tm is None:
            self.logger.warning(
                f"{guid.title_link}: Skipping {guid} not found on Trakt",
                extra={"markup": True},
            )
            return None

        return self.make_media(guid.pm, tm)

    def resolve_trakt(self, tm: TraktItem) -> Media:
        """Find Plex media from Trakt id using Plex Search and Discover"""
        result = self.plex.search_online(tm.item.title, tm.type)
        pm = self._guid_match(result, tm)
        return self.make_media(pm, tm.item)

    def make_media(self, plex: PlexLibraryItem, trakt):
        return Media(plex, trakt, plex_api=self.plex, trakt_api=self.trakt, mf=self)

    def _guid_match(self, candidates: list[PlexLibraryItem], tm: TraktItem) -> PlexLibraryItem | None:
        if candidates:
            for pm in candidates:
                for guid in pm.guids:
                    for provider in ["tmdb", "imdb", "tvdb"]:
                        if guid.provider == provider and hasattr(tm.item, provider) and guid.id == str(getattr(tm.item, provider)):
                            return pm
        return None
