from typing import Union

from trakt.movies import Movie
from trakt.tv import TVEpisode

from plextraktsync.config import Config
from plextraktsync.decorators.cached_property import cached_property
from plextraktsync.events import (ActivityNotification, Error,
                                  PlaySessionStateNotification, TimelineEntry)
from plextraktsync.factory import factory, logging
from plextraktsync.media import Media, MediaFactory
from plextraktsync.plex_api import PlexApi, PlexLibraryItem
from plextraktsync.trakt_api import TraktApi


class ScrobblerCollection(dict):
    def __init__(self, trakt: TraktApi, threshold=80):
        super().__init__()
        self.trakt = trakt
        self.threshold = threshold

    def __missing__(self, key: Union[Movie, TVEpisode]):
        self[key] = value = self.trakt.scrobbler(key, self.threshold)
        return value


class SessionCollection(dict):
    def __init__(self, plex: PlexApi):
        super().__init__()
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


ICONS = {
    "playing": "▶️",
    "paused": "⏸️",
}


class ProgressBar(dict):
    @cached_property
    def progress(self):
        from rich.progress import (BarColumn, Progress, TextColumn,
                                   TimeRemainingColumn)

        from plextraktsync.console import console

        progress = Progress(
            TextColumn("{task.fields[play_state]}  [bold blue]{task.description}", justify="left"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            TimeRemainingColumn(),
            console=console,
        )
        progress.start()

        return progress

    def __missing__(self, m: PlexLibraryItem):
        task = self.progress.add_task(m.title, play_state="")
        self[m] = task

        return task

    def play(self, m: PlexLibraryItem, progress: float):
        task_id = self[m]
        self.progress.update(task_id, completed=progress, play_state=ICONS["playing"])

    def pause(self, m: PlexLibraryItem, progress: float):
        task_id = self[m]
        self.progress.update(task_id, completed=progress, play_state=ICONS["paused"])

    def stop(self, m: PlexLibraryItem):
        task_id = self[m]
        self.progress.remove_task(task_id)
        del self[m]


class WatchStateUpdater:
    def __init__(
        self, plex: PlexApi, trakt: TraktApi, mf: MediaFactory, config: Config
    ):
        self.plex = plex
        self.trakt = trakt
        self.mf = mf
        self.logger = logging.getLogger("PlexTraktSync.WatchStateUpdater")
        self.threshold = config["watch"]["scrobble_threshold"]
        self.remove_collection = config["watch"]["remove_collection"]
        self.add_collection = config["watch"]["add_collection"]
        if config["watch"]["username_filter"]:
            if not self.plex.has_sessions():
                self.logger.warning(
                    "No permission to access sessions, disabling username filter"
                )
                self.username_filter = None
            else:
                self.username_filter = config["PLEX_USERNAME"]
        else:
            self.username_filter = None
        self.sessions = SessionCollection(plex) if self.username_filter else None

    @cached_property
    def scrobblers(self):
        return ScrobblerCollection(self.trakt, self.threshold)

    @cached_property
    def progressbar(self):
        return ProgressBar()

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
        if self.sessions:
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
            self.progressbar.play(m.plex, percent)

            return self.scrobblers[tm].update(percent)

        if state == "paused":
            self.progressbar.pause(m.plex, percent)

            return self.scrobblers[tm].pause(percent)

        if state == "stopped":
            self.progressbar.stop(m.plex)

            value = self.scrobblers[tm].stop(percent)
            del self.scrobblers[tm]
            if self.sessions:
                del self.sessions[event.session_key]
            return value


def watch(server: str):
    factory.run_config.update(
        server=server,
    )
    ws = factory.web_socket_listener
    updater = factory.watch_state_updater

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

    ws.listen()
