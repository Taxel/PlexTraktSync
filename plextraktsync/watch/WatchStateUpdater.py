from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.factory import logging
from plextraktsync.watch.events import (ActivityNotification, Error,
                                        PlaySessionStateNotification,
                                        TimelineEntry)

if TYPE_CHECKING:
    from plextraktsync.config.Config import Config
    from plextraktsync.media import Media, MediaFactory
    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem
    from plextraktsync.trakt.TraktApi import TraktApi


class WatchStateUpdater:
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
        self.logger = logging.getLogger("PlexTraktSync.WatchStateUpdater")
        self.config = config
        self.remove_collection = config["watch"]["remove_collection"]
        self.add_collection = config["watch"]["add_collection"]

    @cached_property
    def username_filter(self):
        if not self.config["watch"]["username_filter"]:
            return None

        if self.plex.has_sessions():
            return self.config["PLEX_USERNAME"]

        self.logger.warning("No permission to access sessions, disabling username filter")
        return None

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

    def find_by_key(self, key: str, reload=False):
        pm: PlexLibraryItem = self.plex.fetch_item(key)

        # Skip excluded libraries
        if pm.library is None:
            return None

        if reload:
            pm = self.plex.reload_item(pm)
        if not pm:
            return None

        m = self.mf.resolve_any(pm)
        if not m:
            return None

        # setup show property for trakt watched status
        if m.is_episode:
            ps = self.plex.fetch_item(m.plex.item.grandparentRatingKey)
            ms = self.mf.resolve_any(ps)
            m.show = ms

        return m

    def on_error(self, error: Error):
        self.logger.error(error.msg)
        self.scrobblers.clear()
        if self.sessions is not None:
            self.sessions.clear()

    def on_activity(self, activity: ActivityNotification):
        m = self.find_by_key(activity.key, reload=True)
        if not m:
            return
        self.logger.info(
            f"on_activity: {m}: Collected: {m.is_collected}, Watched: [Plex: {m.watched_on_plex}, Trakt: {m.watched_on_trakt}]"
        )

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
            return

        m = self.find_by_key(event.key)
        if not m:
            self.logger.debug(f"on_play: Not found: {event.key}")
            return

        movie = m.plex.item
        percent = m.plex.watch_progress(event.view_offset)

        self.logger.info(
            f"on_play: {movie}: {percent:.6F}%, State: {event.state}, Watched: {movie.isPlayed}, LastViewed: {movie.lastViewedAt}"
        )
        scrobbled = self.scrobble(m, percent, event)
        self.logger.debug(f"Scrobbled: {scrobbled}")

    def can_scrobble(self, event: PlaySessionStateNotification):
        if not self.username_filter:
            return True

        return self.sessions[event.session_key] == self.username_filter

    def scrobble(self, m: Media, percent: float, event: PlaySessionStateNotification):
        tm = m.trakt
        state = event.state

        if state == "playing":
            if self.progressbar is not None:
                self.progressbar.play(m.plex, percent)

            return self.scrobblers[tm].update(percent)

        if state == "paused":
            if self.progressbar is not None:
                self.progressbar.pause(m.plex, percent)

            return self.scrobblers[tm].pause(percent)

        if state == "stopped":
            if self.progressbar is not None:
                self.progressbar.stop(m.plex)

            value = self.scrobblers[tm].stop(percent)
            del self.scrobblers[tm]
            if self.sessions is not None:
                del self.sessions[event.session_key]
            return value
