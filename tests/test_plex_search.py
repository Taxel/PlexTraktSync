#!/usr/bin/env python3 -m pytest
from plexapi.server import PlexServer

from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.plex_api import PlexApi

url = CONFIG["PLEX_BASEURL"]
token = CONFIG["PLEX_TOKEN"]
server = PlexServer(url, token)
plex = PlexApi(server)


def test_plex_search():
    search = plex.search("The Addams Family (1964)", libtype="show")
    results = [m for m in search]

    assert len(results) == 1

    m = results[0]
    assert m.type == "show"
    assert m.item.title == "The Addams Family (1964)"
    assert m.provider == "tvdb"
    assert m.id == "77137"
