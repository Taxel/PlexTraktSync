#!/usr/bin/env python3 -m pytest
from __future__ import annotations

from plextraktsync.plan.WalkConfig import WalkConfig
from plextraktsync.plan.WalkPlanner import WalkPlanner
from plextraktsync.plex.PlexApi import PlexApi
from plextraktsync.plex.PlexLibrarySection import PlexLibrarySection


class PlexLibrarySectionMock(PlexLibrarySection):
    def __init__(self, data):
        self.data = data

    def find_by_title(self, name: str):
        items = [item for item in self.data["items"] if item["title"] == name]
        assert len(items) == 1
        return items[0]


class PlexMock(PlexApi):
    def __init__(self, sections):
        self.sections = sections

    def movie_sections(self, library=None):
        by_type = self.sections_by_type("movie", library)
        return by_type

    def show_sections(self, library=None):
        return self.sections_by_type("show", library)

    def sections_by_type(self, libtype, title):
        result = []
        for section in self.sections:
            if section["type"] != libtype:
                continue
            if title and section["title"] != title:
                continue
            result.append(PlexLibrarySectionMock(section))

        return result


def test_walker():
    plex = PlexMock(
        [
            {
                "type": "movie",
                "title": "Movies",
                "items": [
                    {"title": "Batman Begins"},
                ],
            },
            {
                "type": "show",
                "title": "TV Shows",
                "items": [
                    {"title": "Breaking Bad"},
                ],
            },
        ]
    )

    wc = WalkConfig()
    wc.add_library("Movies")
    wc.add_movie("Batman Begins")
    wc.add_library("TV Shows")
    wc.add_show("Breaking Bad")
    plan = WalkPlanner(plex, wc).plan()

    assert len(plan.movie_sections) == 0
    assert len(plan.show_sections) == 0
    assert len(plan.movies) == 1
    assert len(plan.shows) == 1
