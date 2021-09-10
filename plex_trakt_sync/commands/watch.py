import click

from plex_trakt_sync.factory import factory
from plex_trakt_sync.listener import PLAYING, WebSocketListener
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
        self.sessions = {}

    def __call__(self, message):
        for pm, tm, item in self.filter_media(message):
            movie = pm.item
            percent = pm.watch_progress(item["viewOffset"])

            print("%r: %.6F%% Watched: %s, LastViewed: %s" % (
                movie, percent, movie.isWatched, movie.lastViewedAt
            ))

            if factory.config()['watch']['username_filter']:
                if int(item['sessionKey']) not in self.sessions.keys():
                    print("New session: %s" % (item['sessionKey']))
                    self.new_session(int(item['sessionKey']))
                if self.sessions[int(item['sessionKey'])] == factory.config()['PLEX_USERNAME']:
                    self.scrobble(tm, percent, item["state"])
                    print('Scrobbled')
                if item['state'] == "stopped":
                    self.sessions.pop(int(item['sessionKey']))
                    print("Session ended. Remaining sessions: %s" %  (list(self.sessions.keys())))

            else:
                self.scrobble(tm, percent, item["state"])

    def new_session(self, session_key):
        skeys = list(self.sessions.keys())
        for i in skeys:
            if i > session_key:
                 self.sessions.pop(i)

        for session in self.plex.get_sessions():
            if session.sessionKey == session_key:
                self.sessions[session_key] = session.usernames[0]
                break

    def scrobble(self, tm, percent, state):
        if state == "playing":
            return self.scrobblers[tm].update(percent)

        if state == "paused":
            return self.scrobblers[tm].pause()

        if state == "stopped":
            self.scrobblers[tm].stop()
            del self.scrobblers[tm]

    def filter_media(self, message):
        for item in self.filter_playing(message):
            pm = self.plex.fetch_item(int(item["ratingKey"]))
            print(f"Found {pm}")
            if not pm:
                continue

            tm = self.trakt.find_by_media(pm)
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
            if state not in ["playing", "stopped", "paused"]:
                continue

            yield item


@click.command()
def watch():
    """
    Listen to events from Plex
    """

    server = factory.plex_server()
    trakt = factory.trakt_api()
    plex = factory.plex_api()

    ws = WebSocketListener(server)
    ws.on(PLAYING, WatchStateUpdater(plex, trakt))
    print("Listening for events!")
    ws.listen()
