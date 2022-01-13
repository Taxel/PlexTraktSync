import click

from plextraktsync.config import Config
from plextraktsync.events import (ActivityNotification, Error,
                                  PlaySessionStateNotification, TimelineEntry)
from plextraktsync.factory import factory
from plextraktsync.listener import WebSocketListener
from plextraktsync.logging import logging
from plextraktsync.media import Media, MediaFactory
from plextraktsync.plex_api import PlexApi
from plextraktsync.trakt_api import TraktApi


class ScrobblerCollection(dict):
    def __init__(self, trakt: TraktApi, threshold=80):
        super(dict, self).__init__()
        self.trakt = trakt
        self.threshold = threshold

    def __missing__(self, key):
        self[key] = value = self.trakt.scrobbler(key, self.threshold)
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


class WatchStateUpdater:
    def __init__(self, plex: PlexApi, trakt: TraktApi, mf: MediaFactory, config: Config):
        self.plex = plex
        self.trakt = trakt
        self.mf = mf
        self.logger = logging.getLogger("PlexTraktSync.WatchStateUpdater")
        self.scrobblers = ScrobblerCollection(trakt, config["watch"]["scrobble_threshold"])
        self.remove_collection = config["watch"]["remove_collection"]
        self.add_collection = config["watch"]["add_collection"]
        if config["watch"]["username_filter"]:
            self.username_filter = config["PLEX_USERNAME"]
        else:
            self.username_filter = None
        self.sessions = SessionCollection(plex)

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
        self.logger.info(f"Activity: {m}: Collected: {m.is_collected}, Watched: [Plex: {m.watched_on_plex}, Trakt: {m.watched_on_trakt}]")

        if self.add_collection and not m.is_collected:
            self.logger.info(f"Add to collection: {m}")
            m.add_to_collection()
            self.trakt.flush()

    def on_delete(self, event: TimelineEntry):
        self.logger.info(f"Deleted {event.title}")

        m = self.find_by_key(event.item_id)
        if not m:
            return

        if self.remove_collection:
            m.remove_from_collection()
            self.logger.info(f"Removed from Collection: {m}")

    def on_play(self, event: PlaySessionStateNotification):
        if not self.can_scrobble(event):
            return

        m = self.find_by_key(event.key)
        if not m:
            return

        movie = m.plex.item
        percent = m.plex.watch_progress(event.view_offset)

        self.logger.info(f"{movie}: {percent:.6F}% Watched: {movie.isWatched}, LastViewed: {movie.lastViewedAt}")
        self.scrobble(m, percent, event)

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
            return self.scrobblers[tm].pause()

        if state == "stopped":
            self.scrobblers[tm].stop(percent)
            del self.scrobblers[tm]
            del self.sessions[event.session_key]


@click.command()
def watch():
    """
    Listen to events from Plex
    """

    server = factory.plex_server()
    trakt = factory.trakt_api()
    plex = factory.plex_api()
    mf = factory.media_factory()
    config = factory.config()
    ws = WebSocketListener(server)
    updater = WatchStateUpdater(plex, trakt, mf, config)

    ws.on(PlaySessionStateNotification, updater.on_play, state=["playing", "stopped", "paused"])
    ws.on(ActivityNotification, updater.on_activity, type="library.refresh.items", event="ended", progress=100)
    ws.on(TimelineEntry, updater.on_delete, state=9, metadata_state="deleted")
    ws.on(Error, updater.on_error)

    print("Listening for events!")
    ws.listen()
