import json
from os.path import dirname, join as join_path

from plex_trakt_sync.decorators import memoize

MOCK_DATA_DIR = join_path(dirname(__file__), "mock_data")


def load_mock(name: str):
    filename = join_path(MOCK_DATA_DIR, name)
    with open(filename, encoding='utf-8') as f:
        return json.load(f)


@memoize
def get_trakt_api():
    from plex_trakt_sync.trakt_api import TraktApi

    trakt = TraktApi()

    return trakt


@memoize
def get_plex_api():
    from plex_trakt_sync.config import CONFIG
    from plex_trakt_sync.plex_api import PlexApi
    from plexapi.server import PlexServer

    url = CONFIG["PLEX_BASEURL"]
    token = CONFIG["PLEX_TOKEN"]
    server = PlexServer(url, token)
    plex = PlexApi(server)

    return plex


@memoize
def get_media_factory():
    from plex_trakt_sync.media import MediaFactory

    trakt = get_trakt_api()
    plex = get_plex_api()
    mf = MediaFactory(plex, trakt)

    return mf
