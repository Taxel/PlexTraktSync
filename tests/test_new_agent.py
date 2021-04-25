#!/usr/bin/env python3 -m pytest
from plex_trakt_sync.plex_api import PlexLibraryItem
from tests.conftest import get_trakt_api, make

trakt = get_trakt_api()


def test_tv_lookup():
    m = PlexLibraryItem(make(
        cls='plexapi.video.Show',
        guid='plex://show/5d9c085ae98e47001eb0d74f',
        guids=[
            make(id='imdb://tt2661044'),
            make(id='tmdb://48866'),
            make(id='tvdb://268592'),
        ],
        type='show',
    ))

    assert m.provider == 'imdb'
    assert m.id == 'tt2661044'
    assert m.type == 'show'


def test_tv_lookup_none():
    m = PlexLibraryItem(make(
        cls='plexapi.video.Show',
        guid='tv.plex.agents.none://68178',
        guids=[
        ],
        type='show',
    ))

    assert m.provider == 'none'
    assert m.id == '68178'
    assert m.type == 'show'
