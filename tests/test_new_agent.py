#!/usr/bin/env python3 -m pytest
from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem
from tests.conftest import factory, make

trakt = factory.trakt_api


def test_tv_lookup():
    m = PlexLibraryItem(
        make(
            cls="plexapi.video.Show",
            guid="plex://show/5d9c085ae98e47001eb0d74f",
            guids=[
                make(id="imdb://tt2661044"),
                make(id="tmdb://48866"),
                make(id="tvdb://268592"),
            ],
            type="show",
        )
    )

    guid = m.guids[0]

    assert guid.provider == "tmdb"
    assert guid.id == "48866"
    assert m.type == "show"


def test_tv_lookup_none():
    m = PlexLibraryItem(
        make(
            cls="plexapi.video.Show",
            guid="tv.plex.agents.none://68178",
            guids=[],
            type="show",
        )
    )

    guid = m.guids[0]

    assert guid.provider == "none"
    assert guid.id == "68178"
    assert m.type == "show"
