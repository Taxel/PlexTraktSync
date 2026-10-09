#!/usr/bin/env python3 -m pytest
from __future__ import annotations

from plextraktsync.sync.WatchlistMirror import Presence, plan_changes

BOTH = Presence(trakt=True, plex=True)
TRAKT_ONLY = Presence(trakt=True, plex=False)
PLEX_ONLY = Presence(trakt=False, plex=True)


def test_added_on_trakt_is_added_to_plex():
    plan = plan_changes({}, {"movies:1": TRAKT_ONLY}, allow_removals=True)

    assert plan.add_to_plex == {"movies:1"}
    assert plan.remove_from_trakt == set()


def test_added_on_plex_is_added_to_trakt():
    plan = plan_changes({}, {"movies:1": PLEX_ONLY}, allow_removals=True)

    assert plan.add_to_trakt == {"movies:1"}
    assert plan.remove_from_plex == set()


def test_removed_on_trakt_is_removed_from_plex():
    plan = plan_changes({"movies:1": BOTH}, {"movies:1": PLEX_ONLY}, allow_removals=True)

    assert plan.remove_from_plex == {"movies:1"}
    assert plan.add_to_trakt == set()


def test_removed_on_plex_is_removed_from_trakt():
    plan = plan_changes({"movies:1": BOTH}, {"movies:1": TRAKT_ONLY}, allow_removals=True)

    assert plan.remove_from_trakt == {"movies:1"}
    assert plan.add_to_plex == set()


def test_unmatchable_item_absent_from_plex_in_both_states_is_left_alone():
    """A Trakt item Plex Discover has no entry for must never be touched."""
    plan = plan_changes({"shows:9": TRAKT_ONLY}, {"shows:9": TRAKT_ONLY}, allow_removals=True)

    assert not plan.has_changes


def test_removed_from_both_sides_is_a_noop():
    plan = plan_changes({"movies:1": BOTH}, {}, allow_removals=True)

    assert not plan.has_changes


def test_unchanged_item_is_a_noop():
    plan = plan_changes({"movies:1": BOTH}, {"movies:1": BOTH}, allow_removals=True)

    assert not plan.has_changes


def test_movies_and_shows_with_same_trakt_id_are_distinct():
    previous = {"movies:1": BOTH, "shows:1": BOTH}
    current = {"movies:1": BOTH, "shows:1": TRAKT_ONLY}

    plan = plan_changes(previous, current, allow_removals=True)

    assert plan.remove_from_trakt == {"shows:1"}


def test_add_beats_a_conflicting_removal():
    """Added on Trakt while removed on Plex: the add wins, nothing is deleted."""
    plan = plan_changes({"movies:1": PLEX_ONLY}, {"movies:1": TRAKT_ONLY}, allow_removals=True)

    assert plan.add_to_plex == {"movies:1"}
    assert plan.remove_from_trakt == set()


def test_removals_suppressed_when_not_allowed():
    plan = plan_changes(
        {"movies:1": BOTH},
        {"movies:1": PLEX_ONLY},
        allow_removals=False,
        suppress_reason="plex watchlist was empty",
    )

    assert plan.remove_from_plex == set()
    assert plan.suppressed_removals == 1
    assert plan.suppress_reason == "plex watchlist was empty"


def test_adds_still_happen_when_removals_are_suppressed():
    previous = {"movies:1": BOTH}
    current = {"movies:1": PLEX_ONLY, "movies:2": TRAKT_ONLY}

    plan = plan_changes(previous, current, allow_removals=False, suppress_reason="x")

    assert plan.add_to_plex == {"movies:2"}
    assert plan.remove_from_plex == set()


def test_max_delete_cap_suppresses_all_removals():
    previous = {f"movies:{i}": BOTH for i in range(10)}
    current = {f"movies:{i}": TRAKT_ONLY for i in range(10)}

    plan = plan_changes(previous, current, allow_removals=True, max_delete=2)

    assert plan.remove_from_trakt == set()
    assert plan.suppressed_removals == 10
    assert "exceeds" in plan.suppress_reason


def test_removals_within_cap_are_kept():
    previous = {f"movies:{i}": BOTH for i in range(10)}
    current = {**{f"movies:{i}": BOTH for i in range(9)}, "movies:9": TRAKT_ONLY}

    plan = plan_changes(previous, current, allow_removals=True, max_delete=2)

    assert plan.remove_from_trakt == {"movies:9"}
    assert plan.suppressed_removals == 0
