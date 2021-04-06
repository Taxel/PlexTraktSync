import click
from plexapi.server import PlexServer

from plex_trakt_sync.listener import WebSocketListener, PLAYING
from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.plex_api import PlexApi
from plex_trakt_sync.trakt_api import TraktApi


class WatchStateUpdater:
    def __init__(self, plex: PlexApi, trakt: TraktApi):
        self.plex = plex
        self.trakt = trakt

    def __call__(self, message):
        for pm, tm, item in self.filter_media(message):
            movie = pm.item
            percent = pm.watch_progress(item["viewOffset"])

            print("%r: %.6F%% Watched: %s, LastViewed: %s" % (
                movie, percent, movie.isWatched, movie.lastViewedAt
            ))

            self.trakt.scrobble(tm, percent)

    def filter_media(self, message):
        for item in self.filter_playing(message):
            pm = self.plex.fetch_item(item["ratingKey"])
            print(f"Found {pm}")
            if not pm:
                continue

            tm = self.trakt.find_movie(pm)
            if not tm:
                continue

            yield pm, tm, item

    def filter_playing(self, message):
        """
            {'sessionKey': '23', 'guid': '', 'ratingKey': '9725', 'url': '', 'key': '/library/metadata/9725', 'viewOffset': 0, 'playQueueItemID': 17679, 'state': 'playing'}
            {'sessionKey': '23', 'guid': '', 'ratingKey': '9725', 'url': '', 'key': '/library/metadata/9725', 'viewOffset': 10000, 'playQueueItemID': 17679, 'state': 'playing', 'transcodeSession': '18nyclub53k1ey37jjbg8ok3'}
            {'sessionKey': '23', 'guid': '', 'ratingKey': '9725', 'url': '', 'key': '/library/metadata/9725', 'viewOffset': 20000, 'playQueueItemID': 17679, 'state': 'playing', 'transcodeSession': '18nyclub53k1ey37jjbg8ok3'}
            {'sessionKey': '23', 'guid': '', 'ratingKey': '9725', 'url': '', 'key': '/library/metadata/9725', 'viewOffset': 30000, 'playQueueItemID': 17679, 'state': 'playing', 'transcodeSession': '18nyclub53k1ey37jjbg8ok3'}
            {'sessionKey': '23', 'guid': '', 'ratingKey': '9725', 'url': '', 'key': '/library/metadata/9725', 'viewOffset': 30000, 'playQueueItemID': 17679, 'state': 'paused', 'transcodeSession': '18nyclub53k1ey37jjbg8ok3'}
            {'sessionKey': '23', 'guid': '', 'ratingKey': '9725', 'url': '', 'key': '/library/metadata/9725', 'viewOffset': 30000, 'playQueueItemID': 17679, 'state': 'paused', 'transcodeSession': '18nyclub53k1ey37jjbg8ok3'}
        """

        if message["size"] != 1:
            raise ValueError("Unexpected size: %r" % message)

        for item in message["PlaySessionStateNotification"]:
            state = item["state"]
            print(f"State: {state}")
            # "playing", 'buffering', 'stopped'
            if state not in ["playing", "stopped"]:
                continue

            yield item


@click.command()
def watch():
    """
    Listen to events from Plex
    """

    url = CONFIG["PLEX_BASEURL"]
    token = CONFIG["PLEX_TOKEN"]
    server = PlexServer(url, token)
    trakt = TraktApi()
    plex = PlexApi(server)

    ws = WebSocketListener(server)
    ws.on(PLAYING, WatchStateUpdater(plex, trakt))
    print("Listening for events!")
    ws.listen()
