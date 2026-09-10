#!/usr/bin/env python3 -m pytest
from __future__ import annotations

import asyncio

from plextraktsync.sync.WatchlistMirror import Presence
from plextraktsync.sync.WatchlistMirrorPlugin import WatchlistMirrorPlugin

BOTH = Presence(trakt=True, plex=True)
TRAKT_ONLY = Presence(trakt=True, plex=False)


class MediaStub:
    def __init__(self, trakt_id, media_type="movies", on_plex=True):
        self.trakt_id = trakt_id
        self.media_type = media_type
        self.plex = object() if on_plex else None
        self.calls = []

    @property
    def title_link(self):
        return f"{self.media_type}:{self.trakt_id}"

    def add_to_plex_watchlist(self):
        self.calls.append("add_plex")

    def add_to_trakt_watchlist(self):
        self.calls.append("add_trakt")

    def remove_from_plex_watchlist(self):
        self.calls.append("remove_plex")

    def remove_from_trakt_watchlist(self):
        self.calls.append("remove_trakt")


class WalkerStub:
    def __init__(self, plex_media, trakt_media):
        self._plex_media = plex_media
        self._trakt_media = trakt_media
        self.config = type("WalkConfig", (object,), {"walk_watchlist": True})()

    async def media_from_plexlist(self, _):
        for m in self._plex_media:
            yield m

    async def media_from_traktlist(self, _):
        for m in self._trakt_media:
            yield m


class StateStub:
    def __init__(self, items=None, seeded=False):
        self._items = items or {}
        self.is_seeded = seeded
        self.saved = None

    def load(self):
        return dict(self._items), "2026-09-09T00:00:00+00:00"

    def save(self, items):
        self.saved = items


def build(state, plex_media, trakt_media, plex_count=None, max_delete_percent=10):
    plugin = WatchlistMirrorPlugin.__new__(WatchlistMirrorPlugin)
    plugin.state = state
    plugin.max_delete_percent = max_delete_percent
    # The raw watchlists only need a length and to be iterable; the walker stub
    # decides what actually resolves out of them.
    plugin.__dict__["plex_wl"] = list(range(len(plex_media) if plex_count is None else plex_count))
    plugin.__dict__["trakt_wl"] = list(range(len(trakt_media)))

    return plugin, WalkerStub(plex_media, trakt_media)


def run(plugin, walker, dry_run=False):
    asyncio.run(plugin.mirror_watchlist(walker, dry_run=dry_run))


def test_first_run_seeds_without_deleting():
    on_plex_only = MediaStub(1)
    on_trakt_only = MediaStub(2)
    state = StateStub(seeded=False)
    plugin, walker = build(state, [on_plex_only], [on_trakt_only])

    run(plugin, walker)

    assert "remove_trakt" not in on_plex_only.calls
    assert "remove_plex" not in on_trakt_only.calls
    assert state.saved is not None


def test_removal_on_plex_propagates_to_trakt():
    item = MediaStub(1)
    keeper = MediaStub(2)
    state = StateStub({"movies:1": BOTH, "movies:2": BOTH}, seeded=True)
    # Plex still lists the keeper; item 1 is gone from Plex but still on Trakt
    plugin, walker = build(state, [keeper], [item, keeper])

    run(plugin, walker)

    assert item.calls == ["remove_trakt"]
    assert keeper.calls == []


def test_removal_on_trakt_propagates_to_plex():
    item = MediaStub(1)
    keeper = MediaStub(2)
    state = StateStub({"movies:1": BOTH, "movies:2": BOTH}, seeded=True)
    # Trakt still lists the keeper; item 1 is gone from Trakt but still on Plex
    plugin, walker = build(state, [item, keeper], [keeper])

    run(plugin, walker)

    assert item.calls == ["remove_plex"]
    assert keeper.calls == []


def test_addition_on_trakt_propagates_to_plex():
    item = MediaStub(2)
    state = StateStub({"movies:1": BOTH}, seeded=True)
    plugin, walker = build(state, [MediaStub(1)], [item, MediaStub(1)])

    run(plugin, walker)

    assert item.calls == ["add_plex"]


def test_unresolvable_plex_item_suppresses_removals():
    """A Plex entry the walker could not match must not read as a deletion."""
    item = MediaStub(1)
    state = StateStub({"movies:1": BOTH}, seeded=True)
    # 3 raw Plex watchlist entries, but the walker resolves none of them
    plugin, walker = build(state, [], [item], plex_count=3)

    run(plugin, walker)

    assert item.calls == []


def test_empty_plex_watchlist_suppresses_removals():
    item = MediaStub(1)
    state = StateStub({"movies:1": BOTH}, seeded=True)
    plugin, walker = build(state, [], [item], plex_count=0)

    run(plugin, walker)

    assert item.calls == []


def test_empty_trakt_watchlist_suppresses_removals():
    item = MediaStub(1)
    state = StateStub({"movies:1": BOTH}, seeded=True)
    plugin, walker = build(state, [item], [])
    plugin.__dict__["trakt_wl"] = []

    run(plugin, walker)

    assert item.calls == []


def test_item_not_on_plex_discover_is_never_removed():
    item = MediaStub(9, media_type="shows", on_plex=False)
    state = StateStub({"shows:9": TRAKT_ONLY}, seeded=True)
    plugin, walker = build(state, [], [item], plex_count=1)
    # one Plex entry that does resolve, so the shortfall gate does not fire
    walker._plex_media = [MediaStub(1)]
    state._items["movies:1"] = BOTH

    run(plugin, walker)

    assert item.calls == []


def test_mass_delete_cap_suppresses_removals():
    items = [MediaStub(i) for i in range(20)]
    state = StateStub({f"movies:{i}": BOTH for i in range(20)}, seeded=True)
    plugin, walker = build(state, [], items, plex_count=20)
    # walker resolves nothing from Plex would trip the shortfall gate, so give it
    # a full Plex resolution and instead drop every item from Trakt
    walker._plex_media = items
    walker._trakt_media = []
    plugin.__dict__["trakt_wl"] = [0]

    run(plugin, walker)

    assert all(m.calls == [] for m in items)


def test_dry_run_makes_no_calls_and_saves_no_state():
    item = MediaStub(1)
    state = StateStub({"movies:1": BOTH}, seeded=True)
    plugin, walker = build(state, [], [item], plex_count=1)

    run(plugin, walker, dry_run=True)

    assert item.calls == []
    assert state.saved is None
