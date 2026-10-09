#!/usr/bin/env python3 -m pytest
from __future__ import annotations

import json

from plextraktsync.sync.WatchlistMirror import Presence
from plextraktsync.sync.WatchlistState import WatchlistState

BOTH = Presence(trakt=True, plex=True)


def test_missing_file_reads_as_unseeded(tmp_path):
    state = WatchlistState(str(tmp_path / "nope.json"), scope="m1|user")

    items, synced_at = state.load()

    assert items == {}
    assert synced_at is None
    assert state.is_seeded is False


def test_roundtrip(tmp_path):
    path = str(tmp_path / "state.json")
    WatchlistState(path, scope="m1|user").save({"movies:1": BOTH, "shows:2": Presence(trakt=True)})

    reloaded = WatchlistState(path, scope="m1|user")
    items, synced_at = reloaded.load()

    assert items == {"movies:1": BOTH, "shows:2": Presence(trakt=True, plex=False)}
    assert synced_at is not None
    assert reloaded.is_seeded is True


def test_scopes_are_isolated(tmp_path):
    path = str(tmp_path / "state.json")
    WatchlistState(path, scope="m1|user").save({"movies:1": BOTH})
    WatchlistState(path, scope="m2|user").save({"movies:2": BOTH})

    assert WatchlistState(path, scope="m1|user").load()[0] == {"movies:1": BOTH}
    assert WatchlistState(path, scope="m2|user").load()[0] == {"movies:2": BOTH}


def test_corrupt_file_reads_as_unseeded(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{not json at all")

    state = WatchlistState(str(path), scope="m1|user")

    assert state.load() == ({}, None)
    assert state.is_seeded is False


def test_future_schema_version_reads_as_unseeded(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"version": 999, "scopes": {}}))

    assert WatchlistState(str(path), scope="m1|user").load() == ({}, None)


def test_save_preserves_other_scopes(tmp_path):
    path = str(tmp_path / "state.json")
    WatchlistState(path, scope="m1|user").save({"movies:1": BOTH})
    WatchlistState(path, scope="m2|user").save({"movies:2": BOTH})
    WatchlistState(path, scope="m2|user").save({"movies:3": BOTH})

    assert WatchlistState(path, scope="m1|user").load()[0] == {"movies:1": BOTH}
    assert WatchlistState(path, scope="m2|user").load()[0] == {"movies:3": BOTH}


def test_unknown_scope_reads_as_unseeded(tmp_path):
    path = str(tmp_path / "state.json")
    WatchlistState(path, scope="m1|user").save({"movies:1": BOTH})

    other = WatchlistState(path, scope="other|user")

    assert other.load() == ({}, None)
    assert other.is_seeded is False
