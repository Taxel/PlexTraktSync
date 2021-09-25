import click

from plex_trakt_sync.events import PlaySessionStateNotification
from plex_trakt_sync.factory import factory
from plex_trakt_sync.listener import WebSocketListener
from plex_trakt_sync.plex_api import PlexApi
from plex_trakt_sync.trakt_api import TraktApi


class ScrobblerCollection(dict):
    def __init__(self, trakt: TraktApi):
        super(dict, self).__init__()
        self.trakt = trakt

    def __missing__(self, key):
        self[key] = value = self.trakt.scrobbler(key)
        return value


class WatchStateUpdater:
    def __init__(self, plex: PlexApi, trakt: TraktApi):
        self.plex = plex
        self.trakt = trakt
        self.scrobblers = ScrobblerCollection(trakt)

    def on_play(self, event: PlaySessionStateNotification):
        pm = self.plex.fetch_item(event.key)
        print(f"Found {pm}")
        if not pm:
            return

        tm = self.trakt.find_by_media(pm)
        if not tm:
            return

        movie = pm.item
        percent = pm.watch_progress(event.view_offset)

        print(f"{movie}: {percent:.6F}% Watched: {movie.isWatched}, LastViewed: {movie.lastViewedAt}")

        self.scrobble(tm, percent, event.state)

    def scrobble(self, tm, percent, state):
        if state == "playing":
            return self.scrobblers[tm].update(percent)

        if state == "paused":
            return self.scrobblers[tm].pause()

        if state == "stopped":
            self.scrobblers[tm].stop()
            del self.scrobblers[tm]


@click.command()
def watch():
    """
    Listen to events from Plex
    """

    server = factory.plex_server()
    trakt = factory.trakt_api()
    plex = factory.plex_api()

    ws = WebSocketListener(server)
    updater = WatchStateUpdater(plex, trakt)
    ws.on(PlaySessionStateNotification, updater.on_play, state=["playing", "stopped", "paused"])

    print("Listening for events!")
    ws.listen()
