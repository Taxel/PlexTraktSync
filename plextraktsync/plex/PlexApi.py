from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import plexapi
from plexapi.exceptions import BadRequest, NotFound, Unauthorized
from plexapi.media import SubtitleStream
from plexapi.myplex import MyPlexAccount
from plexapi.playlist import Playlist
from plexapi.server import PlexServer, SystemAccount, SystemDevice

from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.decorators.flatten import flatten_dict, flatten_list
from plextraktsync.decorators.memoize import memoize
from plextraktsync.decorators.nocache import nocache
from plextraktsync.decorators.retry import retry
from plextraktsync.factory import factory, logger
from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem
from plextraktsync.plex.PlexLibrarySection import PlexLibrarySection

if TYPE_CHECKING:
    from typing import Dict, List, Optional, Union

    from plexapi.video import Movie, Show

    from plextraktsync.plex.types import PlexMedia


class PlexApi:
    """
    Plex API class abstracting common data access and dealing with requests cache.
    """

    def __init__(self, plex: PlexServer):
        self.plex = plex

    @cached_property
    def account(self):
        return self._plex_account()

    @cached_property
    def plex_base_url(self):
        return f"https://app.plex.tv/desktop/#!/server/{self.plex.machineIdentifier}"

    @flatten_list
    def movie_sections(self, library=None) -> List[PlexLibrarySection]:
        for section in self.library_sections.values():
            if section.type != "movie":
                continue
            if library and section.title != library:
                continue
            yield section

    @flatten_list
    def show_sections(self, library=None) -> List[PlexLibrarySection]:
        for section in self.library_sections.values():
            if section.type != "show":
                continue
            if library and section.title != library:
                continue
            yield section

    @memoize
    @nocache
    @retry()
    def fetch_item(self, key: Union[int, str]) -> Optional[PlexLibraryItem]:
        try:
            media = self.plex.library.fetchItem(key)
        except NotFound:
            return None

        return PlexLibraryItem(media, plex=self)

    def reload_item(self, pm: PlexLibraryItem):
        try:
            key = pm.item.ratingKey
        except AttributeError as e:
            logger.debug(f"Invalid object: {e}")
            return None

        self.fetch_item.cache_clear()

        return self.fetch_item(key)

    def media_url(self, m: PlexLibraryItem):
        return f"{self.plex_base_url}/details?key={m.item.key}"

    def download(self, m: Union[SubtitleStream], **kwargs):
        url = self.plex.url(m.key)
        token = self.plex._token

        return plexapi.utils.download(url, token, **kwargs)

    def search(self, title: str, **kwargs):
        result = self.plex.library.search(title, **kwargs)
        for media in result:
            yield PlexLibraryItem(media, plex=self)

    @cached_property
    @nocache
    def version(self):
        return self.plex.version

    @cached_property
    @nocache
    def updated_at(self):
        return self.plex.updatedAt

    @cached_property
    @nocache
    @flatten_dict
    def library_sections(self) -> Dict[int, PlexLibrarySection]:
        excluded_libraries = factory.config["excluded-libraries"]
        for section in self.plex.library.sections():
            if section.title in excluded_libraries:
                continue
            yield section.key, PlexLibrarySection(section, plex=self)

    @property
    def library_section_names(self):
        return [s.title for s in self.library_sections.values()]

    @memoize
    @nocache
    def system_device(self, device_id: int) -> SystemDevice:
        return self.plex.systemDevice(device_id)

    @memoize
    @nocache
    def system_account(self, account_id: int) -> SystemAccount:
        return self.plex.systemAccount(account_id)

    @cached_property
    def ratings(self):
        from plextraktsync.plex.PlexRatings import PlexRatings

        return PlexRatings(self)

    @nocache
    @retry()
    def rate(self, m, rating):
        m.rate(rating)

    @staticmethod
    def same_list(list_a: List[PlexMedia], list_b: List[PlexMedia]) -> bool:
        """
        Return true if two list contain same Plex items.
        The comparison is made on ratingKey property,
        the items don't have to actually be identical.
        """

        # Quick way out of lists with different length
        if len(list_a) != len(list_b):
            return False

        a = [m.ratingKey for m in list_a]
        b = [m.ratingKey for m in list_b]

        return a == b

    @nocache
    def update_playlist(self, name: str, items: List[PlexMedia], description=None) -> bool:
        """
        Updates playlist (creates if name missing) replacing contents with items[]
        """
        playlist: Optional[Playlist] = None
        try:
            playlist = self.plex.playlist(name)
        except NotFound:
            if len(items) > 0:
                playlist = self.plex.createPlaylist(name, items=items)

        # Skip if playlist could not be made/retrieved
        if playlist is None:
            return False

        updated = False
        if description is not None and description != playlist.summary:
            playlist.edit(summary=description)
            updated = True

        # Skip if nothing to update
        if self.same_list(items, playlist.items()):
            return updated

        playlist.removeItems(playlist.items())
        playlist.addItems(items)
        return True

    @nocache
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

    @nocache
    @retry()
    def mark_watched(self, m):
        m.markPlayed()

    @nocache
    @retry()
    def mark_unwatched(self, m):
        m.markUnplayed()

    @nocache
    def has_sessions(self):
        try:
            self.plex.sessions()
            return True
        except Unauthorized:
            return False

    @nocache
    def get_sessions(self):
        return self.plex.sessions()

    @nocache
    def _plex_account(self):
        CONFIG = factory.config
        plex_owner_token = CONFIG.get("PLEX_OWNER_TOKEN")
        plex_account_token = CONFIG.get("PLEX_ACCOUNT_TOKEN")
        plex_username = CONFIG.get("PLEX_USERNAME")
        if plex_owner_token:
            try:
                plex_owner_account = MyPlexAccount(token=plex_owner_token)
                return plex_owner_account.switchHomeUser(plex_username)
            except BadRequest as e:
                logger.error(f"Error during {plex_username} account access: {e}")
        elif plex_account_token:
            try:
                return MyPlexAccount(token=plex_account_token)
            except BadRequest as e:
                logger.error(f"Error during {plex_username} account access: {e}")
        else:
            try:
                return self.plex.myPlexAccount()
            except BadRequest as e:
                logger.error(f"Error during {plex_username} account access: {e}")
        return None

    @nocache
    def watchlist(self) -> Optional[List[Union[Movie, Show]]]:
        if self.account:
            try:
                return self.account.watchlist()
            except BadRequest as e:
                logger.error(f"Error during {self.account.username} watchlist access: {e}")
        return None

    @nocache
    def add_to_watchlist(self, item):
        try:
            self.account.addToWatchlist(item)
        except BadRequest as e:
            logger.error(f"Error when adding {item.title} to Plex watchlist: {e}")

    @nocache
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

    @nocache
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
