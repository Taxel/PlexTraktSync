import click
from plexapi.server import PlexServer
from plex_trakt_sync.listener import WebSocketListener, PLAYING
from plex_trakt_sync.config import CONFIG


class WatchStateUpdater:
    def __init__(self, plex):
        self.plex = plex

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

            viewOffset = item["viewOffset"]
            ratingKey = item["ratingKey"]
            print("Find movie for %s @ %s" % (ratingKey, viewOffset))
            movie = self.plex.library.fetchItem("/library/metadata/%s" % ratingKey)
            print("Found movie: %r" % movie)
            percent = viewOffset/movie.duration * 100

            print("%r: %.6F%% Duration: %s, Watched: %s, LastViewed: %s" % (
                movie, percent, movie.duration, movie.isWatched, movie.lastViewedAt
            ))


@click.command()
def watch():
    """
    Listen to events from Plex
    """

    url = CONFIG["PLEX_BASEURL"]
    token = CONFIG["PLEX_TOKEN"]
    server = PlexServer(url, token)

    ws = WebSocketListener(server)
    ws.on(PLAYING, WatchStateUpdater(server))
    print("Listening for events!")
    ws.listen()
