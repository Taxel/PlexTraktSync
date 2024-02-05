from __future__ import annotations

from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING

import plexapi
from plexapi.exceptions import BadRequest, NotFound, Unauthorized
from plexapi.myplex import MyPlexAccount
from plexapi.server import SystemAccount, SystemDevice

from plextraktsync.decorators.flatten import flatten_dict, flatten_list
from plextraktsync.decorators.memoize import memoize
from plextraktsync.decorators.retry import retry
from plextraktsync.factory import factory, logger
from plextraktsync.plex.PlexId import PlexId
from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem
from plextraktsync.plex.PlexLibrarySection import PlexLibrarySection

if TYPE_CHECKING:
    from plexapi.media import MediaPart, SubtitleStream
    from plexapi.server import PlexServer
    from plexapi.video import Movie, Show

    from plextraktsync.config.PlexServerConfig import PlexServerConfig
    from plextraktsync.plex.types import PlexMedia


class PlexApi:
    """
    Plex API class abstracting common data access and dealing with requests cache.
    """

    def __init__(
            self,
            server: PlexServer,
            config: PlexServerConfig,
    ):
        self.server = server
        self.config = config

    def __str__(self):
        return str(self.server)

    def plex_base_url(self, section="server"):
        return f"https://app.plex.tv/desktop/#!/{section}/{self.server.machineIdentifier}"

    @property
    def plex_discover_base_url(self):
        return "https://app.plex.tv/desktop/#!/provider/tv.plex.provider.discover"

    @flatten_list
    def movie_sections(self, library=None) -> list[PlexLibrarySection]:
        for section in self.library_sections.values():
            if section.type != "movie":
                continue
            if library and section.title != library:
                continue
            yield section

    @flatten_list
    def show_sections(self, library=None) -> list[PlexLibrarySection]:
        for section in self.library_sections.values():
            if section.type != "show":
                continue
            if library and section.title != library:
                continue
            yield section

    @retry()
    def fetch_item(self, key: int | str | PlexId) -> PlexLibraryItem | None:
        try:
            if isinstance(key, PlexId):
                plex_id = key
                if plex_id.is_discover:
                    # https://github.com/pkkid/python-plexapi/issues/1091
                    account = self.account
                    media = account.fetchItem(key.metadata_url)
                    media = account._toOnlineMetadata(media)[0]
                else:
                    media = self.server.library.fetchItem(plex_id.key)
            else:
                media = self.server.library.fetchItem(key)
        except NotFound:
            return None

        return PlexLibraryItem(media, plex=self)

    def media_url(self, m: PlexLibraryItem, discover=False):
        base_url = self.plex_discover_base_url if m.is_discover or discover else self.plex_base_url("server")
        key = f"/library/metadata/{m.item.guid.rsplit('/', 1)[-1]}" if discover else m.item.key

        return f"{base_url}/details?key={key}"

    def download(self, m: SubtitleStream | MediaPart, **kwargs):
        url = self.server.url(m.key)
        token = self.server._token

        return plexapi.utils.download(url, token, **kwargs)

    @property
    def version(self):
        return self.server.version

    @property
    def updated_at(self):
        return self.server.updatedAt

    @cached_property
    @flatten_dict
    def library_sections(self) -> dict[int, PlexLibrarySection]:
        enabled_libraries = self.config.libraries

        # If server has defined libraries, ignore global "excluded libraries"
        # otherwise merge server excluded libraries with global excluded libraries
        if enabled_libraries is not None:
            excluded_libraries = self.config.excluded_libraries or []
        else:
            excluded_libraries = factory.config["excluded-libraries"] + (self.config.excluded_libraries or [])

        for section in self.server.library.sections():
            if enabled_libraries is not None:
                if section.title not in enabled_libraries:
                    continue
            if section.title in excluded_libraries:
                continue

            yield section.key, PlexLibrarySection(section, plex=self)

    @memoize
    def system_device(self, device_id: int) -> SystemDevice:
        return self.server.systemDevice(device_id)

    @memoize
    def system_account(self, account_id: int) -> SystemAccount:
        return self.server.systemAccount(account_id)

    @cached_property
    def ratings(self):
        from plextraktsync.plex.PlexRatings import PlexRatings

        return PlexRatings(self)

    @retry()
    def rate(self, m, rating):
        m.rate(rating)

    def update_playlist(self, name: str, items: list[PlexMedia], description=None) -> bool:
        """
        Updates playlist (creates if name missing) replacing contents with items[]
        """
        from plextraktsync.plex.PlexPlaylist import PlexPlaylist

        playlist = PlexPlaylist(self.server, name)

        return playlist.update(items, description)

    @flatten_list
    def history(self, m, device=False, account=False):
        try:
            history = m.history()
        except Unauthorized as e:
            logger.debug(f"No permission to access play history: {e}")
            return

        for h in history:
            if device:
                h.device = self.system_device(h.deviceID)
            if account:
                h.account = self.system_account(h.accountID)
            yield h

    @retry()
    def mark_watched(self, m):
        m.markPlayed()

    @retry()
    def mark_unwatched(self, m):
        m.markUnplayed()

    def has_sessions(self):
        try:
            self.server.sessions()
            return True
        except Unauthorized:
            return False

    @property
    def sessions(self):
        return self.server.sessions()

    @cached_property
    def account(self):
        CONFIG = factory.config
        plex_owner_token = CONFIG.get("PLEX_OWNER_TOKEN")
        plex_account_token = CONFIG.get("PLEX_ACCOUNT_TOKEN")
        plex_username = CONFIG.get("PLEX_USERNAME")
        if plex_owner_token:
            try:
                plex_owner_account = MyPlexAccount(token=plex_owner_token, session=factory.session)
                return plex_owner_account.switchHomeUser(plex_username)
            except BadRequest as e:
                logger.error(f"Error during {plex_username} account access: {e}")
        elif plex_account_token:
            try:
                return MyPlexAccount(token=plex_account_token, session=factory.session)
            except BadRequest as e:
                logger.error(f"Error during {plex_username} account access: {e}")
        else:
            try:
                return self.server.myPlexAccount()
            except BadRequest as e:
                logger.error(f"Error during {plex_username} account access: {e}")
        return None

    def watchlist(self, libtype=None) -> list[Movie | Show] | None:
        if not self.account:
            return None

        params = {
            "includeCollections": 0,
            "includeExternalMedia": 0,
            "includeUserState": 0,
        }
        try:
            return self.account.watchlist(libtype=libtype, **params)
        except BadRequest as e:
            logger.error(f"Error during {self.account.username} watchlist access: {e}")
            return None

    def add_to_watchlist(self, item):
        try:
            self.account.addToWatchlist(item)
        except BadRequest as e:
            logger.error(f"Error when adding {item.title} to Plex watchlist: {e}")

    def remove_from_watchlist(self, item):
        try:
            self.account.removeFromWatchlist(item)
        except BadRequest as e:
            logger.error(f"Error when removing {item.title} from Plex watchlist: {e}")

    @retry()
    def search_online(self, title: str, media_type: str):
        if not self.account:
            return None
        try:
            result = self.account.searchDiscover(title, libtype=media_type)
        except (BadRequest, Unauthorized) as e:
            logger.error(f"{title}: Searching Plex Discover error: {e}")
            return None
        except NotFound:
            return None
        return map(PlexLibraryItem, result)

    def reset_show(self, show: Show, reset_date: datetime):
        reset_count = 0
        for ep in show.watched():
            ep_seen_date = PlexLibraryItem(ep).seen_date.replace(tzinfo=None)
            if ep_seen_date < reset_date:
                self.mark_unwatched(ep)
                reset_count += 1
            else:
                logger.debug(
                    f"{show.title} {ep.seasonEpisode} watched at {ep.lastViewedAt} after reset date {reset_date}")
        logger.debug(f"{show.title}: {reset_count} Plex episode(s) marked as unwatched.")
