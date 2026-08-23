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


class ShowStub:
    """Minimal stand-in for a preloaded PlexLibraryItem show."""

    def __init__(self, key):
        self.key = key

    def __str__(self):
        return f"show:{self.key}"


class EpisodeStub:
    """Minimal stand-in for an episode yielded by the episode pager."""

    def __init__(self, show_id, title):
        self.show_id = show_id
        self.title = title
        self.show = None

    def __str__(self):
        return self.title


class MediaFactoryStub:
    def resolve_any(self, item, show=None):
        return item


class WalkPlanStub:
    def __init__(self):
        self.episodes = None
        self.show_sections = ["section"]


def _walker_with(shows, episodes):
    from plextraktsync.plan.Walker import Walker

    walker = Walker(plex=None, trakt=None, mf=MediaFactoryStub(), config=None)
    walker.__dict__["plan"] = WalkPlanStub()

    async def get_plex_shows():
        for s in shows:
            yield s

    async def episodes_from_sections(_sections):
        for e in episodes:
            yield e

    walker.get_plex_shows = get_plex_shows
    walker.episodes_from_sections = episodes_from_sections
    return walker


async def _collect(walker):
    return [m async for m in walker.find_episodes()]


def test_find_episodes_skips_an_episode_whose_show_was_not_preloaded(caplog):
    """An orphan episode must not abort the whole sync.

    The shows and the episodes come from two independent pagers over a live
    server, so an episode can arrive whose show the first pass never yielded.
    Before this was guarded, that raised KeyError out of find_episodes and
    killed the run (gh-2113).
    """
    import asyncio
    import logging

    known = ShowStub(1)
    walker = _walker_with(
        shows=[known],
        episodes=[
            EpisodeStub(1, "kept-before"),
            EpisodeStub(568765, "orphan"),
            EpisodeStub(1, "kept-after"),
        ],
    )

    with caplog.at_level(logging.WARNING):
        result = asyncio.run(_collect(walker))

    # The orphan is dropped and both good episodes survive, including the one
    # after it: a fix that returned early instead of continuing would lose it.
    assert [str(m) for m in result] == ["kept-before", "kept-after"]
    assert all(m.show is known for m in result)
    assert "568765" in caplog.text
