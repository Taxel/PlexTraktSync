import click
from plexapi.server import PlexServer

from plex_trakt_sync.decorators import memoize
from plex_trakt_sync.listener import WebSocketListener, PLAYING
from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.plex_api import PlexApi, PlexLibraryItem
from plex_trakt_sync.trakt_api import TraktApi


class WatchStateUpdater:
    def __init__(self, plex: PlexApi, trakt: TraktApi):
        self.plex = plex
        self.trakt = trakt

    def __call__(self, message):
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
            print(item)
            state = item["state"]
            # "playing", 'buffering', 'stopped'
            if state == 'buffering':
                continue

            pm = self.plex.fetch_item(item["ratingKey"])
            print(f"Found {pm} for {item['ratingKey']}")
            if not pm:
                continue

            movie = pm.item
            percent = pm.watch_progress(item["viewOffset"])

            print("%r: %.6F%% Duration: %s, Watched: %s, LastViewed: %s" % (
                movie, percent, movie.duration, movie.isWatched, movie.lastViewedAt
            ))

            tm = self.trakt.find_movie(pm)
            if not tm:
                continue

            self.trakt.scrobble(tm, percent)


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
