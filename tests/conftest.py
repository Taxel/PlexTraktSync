import json
from os.path import dirname, join as join_path

MOCK_DATA_DIR = join_path(dirname(__file__), "mock_data")


def load_mock(name: str):
    filename = join_path(MOCK_DATA_DIR, name)
    with open(filename, encoding='utf-8') as f:
        return json.load(f)


def get_plex_api():
    from plex_trakt_sync.config import CONFIG
    from plex_trakt_sync.plex_api import PlexApi
    from plexapi.server import PlexServer

    url = CONFIG["PLEX_BASEURL"]
    token = CONFIG["PLEX_TOKEN"]
    server = PlexServer(url, token)
    plex = PlexApi(server)

    return plex
