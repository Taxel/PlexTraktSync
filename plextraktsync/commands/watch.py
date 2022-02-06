from typing import Union

from trakt.movies import Movie
from trakt.tv import TVEpisode

from plextraktsync.config import Config
from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.events import (
    ActivityNotification,
    Error,
    PlaySessionStateNotification,
    TimelineEntry,
)
from plextraktsync.factory import factory
from plextraktsync.listener import WebSocketListener
from plextraktsync.logging import logging
from plextraktsync.media import Media, MediaFactory
from plextraktsync.plex_api import PlexApi
from plextraktsync.trakt_api import TraktApi


class ScrobblerCollection(dict):
    def __init__(self, trakt: TraktApi, scrobble_movie_threshold: int = 80, scrobble_episode_threshold: int = 80):
        super(dict, self).__init__()
        self.trakt = trakt
        self.episode_threshold = scrobble_episode_threshold
        self.movie_threshold = scrobble_movie_threshold

    def __missing__(self, media: Union[Movie, TVEpisode]):
        if media.media_type == "movies":
            threshold = self.movie_threshold
        elif media.media_type == "episodes":
            threshold = self.episode_threshold
        else:
            raise RuntimeError(f"Unsupported media type {media.media_type}")

        self[media] = value = self.trakt.scrobbler(media, threshold)

        return value


class SessionCollection(dict):
    def __init__(self, plex: PlexApi):
        super(dict, self).__init__()
        self.plex = plex

    def __missing__(self, key: str):
        self.update_sessions()
        if key not in self:
            # Session probably ended
            return None

        return self[key]

    def update_sessions(self):
        sessions = self.plex.get_sessions()
        self.clear()
        for session in sessions:
            self[str(session.sessionKey)] = session.usernames[0]


class WatchConfig:
    def __init__(self, config: Config):
        self.config = dict(config["watch"])
        self.plex_username = config["PLEX_USERNAME"]

    def __getitem__(self, key):
        return self.config[key]

    def __contains__(self, key):
        return key in self.config

    @cached_property
    def username_filter(self):
        if self.config["username_filter"]:
            return self.plex_username

        return None

    @cached_property
    def movie_threshold(self):
        return self.threshold("scrobble_movie_threshold")

    @cached_property
    def episode_threshold(self):
        return self.threshold("scrobble_episode_threshold")

    @cached_property
    def remove_collection(self):
        return self.config["remove_collection"]

    @cached_property
    def add_collection(self):
        return self.config["add_collection"]

    def threshold(self, key: str):
        if "scrobble_threshold" in self.config:
            return self.config["scrobble_threshold"]

        return self.config[key]


class WatchStateUpdater:
    def __init__(
        self, plex: PlexApi, trakt: TraktApi, mf: MediaFactory, config: Config
    ):
        self.plex = plex
        self.trakt = trakt
        self.mf = mf
        self.logger = logging.getLogger("PlexTraktSync.WatchStateUpdater")
        self.config = WatchConfig(config)
        self.username_filter = self.config.username_filter
        if self.username_filter and not self.plex.has_sessions():
            self.logger.warning('No permission to access sessions, disabling username filter')
            self.username_filter = None
        self.sessions = SessionCollection(plex)

    @cached_property
    def scrobblers(self):
        return ScrobblerCollection(self.trakt, self.config.movie_threshold, self.config.episode_threshold)

    def find_by_key(self, key: str, reload=False):
        pm = self.plex.fetch_item(key)
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
        self.sessions.clear()

    def on_activity(self, activity: ActivityNotification):
        m = self.find_by_key(activity.key, reload=True)
        if not m:
            return
        self.logger.info(
            f"on_activity: {m}: Collected: {m.is_collected}, Watched: [Plex: {m.watched_on_plex}, Trakt: {m.watched_on_trakt}]"
        )

        if m.watched_on_plex and not m.watched_on_trakt:
            self.logger.info(
                f"on_activity: Marking {activity.key} as watched in Trakt: {m}"
            )
            m.mark_watched_trakt()

        if self.config.add_collection and not m.is_collected:
            self.logger.info(f"on_activity: Add {activity.key} to collection: {m}")
            m.add_to_collection()

    def on_delete(self, event: TimelineEntry):
        self.logger.info(f"on_delete: Deleted on Plex: {event.item_id}: {event.title}")

        m = self.find_by_key(event.item_id)
        if not m:
            self.logger.error(f"on_delete: Not found: {event.item_id}")
            return

        if self.config.remove_collection:
            m.remove_from_collection()
            self.logger.info(f"on_delete: Removed {event.item_id} from Collection: {m}")

    def on_play(self, event: PlaySessionStateNotification):
        if not self.can_scrobble(event):
            return

        m = self.find_by_key(event.key)
        if not m:
            self.logger.error(f"on_play: Not found: {event.key}")
            return

        movie = m.plex.item
        percent = m.plex.watch_progress(event.view_offset)

        self.logger.info(f"on_play: {event.state} {percent:.6F}% {movie}: Watched: {movie.isWatched}, LastViewed: {movie.lastViewedAt}")
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
            return self.scrobblers[tm].update(percent)

        if state == "paused":
            return self.scrobblers[tm].pause(percent)

        if state == "stopped":
            value = self.scrobblers[tm].stop(percent)
            del self.scrobblers[tm]
            del self.sessions[event.session_key]
            return value


def watch():
    server = factory.plex_server()
    trakt = factory.trakt_api()
    plex = factory.plex_api()
    mf = factory.media_factory()
    config = factory.config()
    ws = WebSocketListener(server)
    updater = WatchStateUpdater(plex, trakt, mf, config)

    ws.on(
        PlaySessionStateNotification,
        updater.on_play,
        state=["playing", "stopped", "paused"],
    )
    ws.on(
        ActivityNotification,
        updater.on_activity,
        type="library.refresh.items",
        event="ended",
        progress=100,
    )
    ws.on(TimelineEntry, updater.on_delete, state=9, metadata_state="deleted")
    ws.on(Error, updater.on_error)

    print("Listening for events!")
    ws.listen()
