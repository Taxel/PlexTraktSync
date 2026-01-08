from __future__ import annotations

from functools import cached_property, lru_cache
from typing import TYPE_CHECKING

from plextraktsync.factory import logging
from plextraktsync.mixin.SetWindowTitle import SetWindowTitle
from plextraktsync.watch.events import (
    ActivityNotification,
    Error,
    PlaySessionStateNotification,
    ServerStarted,
    TimelineEntry,
)

if TYPE_CHECKING:
    from plextraktsync.config.Config import Config
    from plextraktsync.media.Media import Media
    from plextraktsync.media.MediaFactory import MediaFactory
    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem
    from plextraktsync.trakt.TraktApi import TraktApi


class WatchStateUpdater(SetWindowTitle):
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        plex: PlexApi,
        trakt: TraktApi,
        mf: MediaFactory,
        config: Config,
    ):
        self.plex = plex
        self.trakt = trakt
        self.mf = mf
        self.config = config
        self.remove_collection = config["watch"]["remove_collection"]
        self.add_collection = config["watch"]["add_collection"]
        self.session_media = {}

    def clamp_percent(self, percent: float) -> float:
        if percent < 0:
            return 0.0
        if percent > 100:
            return 100.0
        return percent

    @cached_property
    def username_filter(self):
        if not self.config["watch"]["username_filter"]:
            return None

        if self.plex.has_sessions():
            # This must be username, not email
            return self.plex.account.username

        self.logger.warning("No permission to access sessions, disabling username filter")
        return None

    @cached_property
    def ignore_clients(self):
        return self.config["watch"]["ignore_clients"] or []

    @cached_property
    def progressbar(self):
        if not self.config["watch"]["media_progressbar"]:
            return None

        from plextraktsync.watch.ProgressBar import ProgressBar

        return ProgressBar()

    @cached_property
    def sessions(self):
        if not self.username_filter:
            return None

        from plextraktsync.plex.SessionCollection import SessionCollection

        return SessionCollection(self.plex)

    @cached_property
    def scrobblers(self):
        from plextraktsync.trakt.ScrobblerCollection import ScrobblerCollection

        return ScrobblerCollection(self.trakt, self.config["watch"]["scrobble_threshold"])

    @lru_cache(maxsize=2)
    def fetch_item(self, key: str):
        return self.plex.fetch_item(key)

    @lru_cache(maxsize=2)
    def mf_resolve(self, pm: PlexLibraryItem):
        return self.mf.resolve_any(pm)

    def find_by_key(self, key: str, reload=False):
        if reload:
            self.fetch_item.cache_clear()

        pm: PlexLibraryItem = self.fetch_item(key)
        if not pm:
            return None

        # Skip unwanted kind
        if pm.type not in ["episode", "movie"]:
            return None

        # Skip excluded libraries
        if pm.library is None:
            return None

        m = self.mf_resolve(pm)
        if not m:
            return None

        # setup show property for trakt watched status
        if m.is_episode:
            ps = self.fetch_item(m.plex.item.grandparentRatingKey)
            ms = self.mf_resolve(ps)
            m.show = ms

        return m

    @property
    def server(self):
        return self.plex.server

    def on_start(self, event: ServerStarted):
        self.logger.info(f"Server connected: {event.server.friendlyName} ({event.server.version})")
        self.reset_title()

    def reset_title(self):
        self.set_window_title(f"watch: {self.server.friendlyName} ({self.server.version})")

    def on_error(self, error: Error):
        self.logger.error(error.msg)
        self.scrobblers.clear()
        if self.sessions is not None:
            self.sessions.clear()

    def on_activity(self, activity: ActivityNotification):
        # Skip Show ands Seasons view
        if activity.key.endswith("/children"):
            return
        m = self.find_by_key(activity.key, reload=True)
        if not m:
            return
        self.logger.info(f"on_activity: {m}: Collected: {m.is_collected}, Watched: [Plex: {m.watched_on_plex}, Trakt: {m.watched_on_trakt}]")

        if self.add_collection and not m.is_collected:
            self.logger.info(f"on_activity: Add {activity.key} to collection: {m}")
            m.add_to_collection()

    def on_delete(self, event: TimelineEntry):
        self.logger.info(f"on_delete: Deleted on Plex: {event.item_id}: {event.title}")

        m = self.find_by_key(event.item_id)
        if not m:
            self.logger.error(f"on_delete: Not found: {event.item_id}")
            return

        if self.remove_collection:
            m.remove_from_collection()
            self.logger.info(f"on_delete: Removed {event.item_id} from Collection: {m}")

    def on_play(self, event: PlaySessionStateNotification):
        if not self.can_scrobble(event):
            self.logger.debug(f"on_play: Rejected event {event}")
            return

        m = self.find_by_key(event.key)
        if not m:
            self.logger.debug(f"on_play: Not found: {event.key}")
            return
        
        # Bind session → media on first playing event
        bound = self.session_media.get(event.session_key)

        if event.state == "playing":
            if bound is None:
                self.session_media[event.session_key] = m
            else:
                # Ignore spurious "playing" for wrong media
                m = bound

        else:
            # paused / stopped must use bound media
            if bound is None:
                self.logger.debug(
                    "on_play: %s for unknown session %s",
                    event.state,
                    event.session_key,
                )
                return
            m = bound

        movie = m.plex.item
        raw_percent = m.plex.watch_progress(event.view_offset)
        percent = self.clamp_percent(raw_percent)

        if percent != raw_percent:
            self.logger.debug(
                f"on_play: Invalid percent for {m}: raw {raw_percent:.3F}% clamped {percent:.3F}%",
            )

        self.logger.info(f"on_play: {movie}: {percent:.3F}%, State: {event.state}, Played: {movie.isPlayed}, LastViewed: {movie.lastViewedAt}")
        scrobbled = self.scrobble(m, percent, event)

        if event.state == "stopped":
            self.session_media.pop(event.session_key, None)

        self.logger.debug(f"Scrobbled: {scrobbled}")

    def can_scrobble(self, event: PlaySessionStateNotification):
        if self.ignore_clients:
            if event.client_identifier in self.ignore_clients:
                return False

        if not self.username_filter:
            return True

        return self.sessions[event.session_key] == self.username_filter

    def scrobble(self, m: Media, percent: float, event: PlaySessionStateNotification):
        tm = m.trakt
        state = event.state

        if state == "playing":
            if self.progressbar is not None:
                self.progressbar.play(m.plex, percent)
            self.set_window_title(f"Watching {m.title}")

            return self.scrobblers[tm].update(percent)

        if state == "paused":
            if self.progressbar is not None:
                self.progressbar.pause(m.plex, percent)
            self.reset_title()

            return self.scrobblers[tm].pause(percent)

        if state == "stopped":
            if self.progressbar is not None:
                self.progressbar.stop(m.plex)
            self.reset_title()

            value = self.scrobblers[tm].stop(percent)
            del self.scrobblers[tm]
            if self.sessions is not None:
                del self.sessions[event.session_key]
            return value
