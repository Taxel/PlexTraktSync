#!/usr/bin/env python3 -m pytest
from plex_trakt_sync.plex_api import PlexLibraryItem
from tests.conftest import factory, make

trakt = factory.trakt_api()


def test_show_lookup():
    m = PlexLibraryItem(make(
        cls='plexapi.video.Show',
        guid='com.plexapp.agents.hama://tvdb-305074?lang=en',
        guids=[
        ],
        type='show',
    ))

    guid = m.guids[0]

    assert m.type == 'show'
    assert guid.provider == 'tvdb'
    assert guid.id == '305074'
