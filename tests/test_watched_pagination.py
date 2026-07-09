#!/usr/bin/env python3 -m pytest
from __future__ import annotations

import pytest

from plextraktsync import pytrakt_extensions
from plextraktsync.pytrakt_extensions import AllShowsProgress, ShowProgress, allcollected, allwatched


def _show(trakt_id, played=1):
    episodes = [{"number": played, "plays": 1}, {"number": played + 1, "plays": 0}]
    return {"show": {"ids": {"trakt": trakt_id, "slug": f"show-{trakt_id}"}}, "seasons": [{"number": 1, "episodes": episodes}]}


def test_show_progress_marks_only_played_episodes():
    prog = ShowProgress(**_show(1))
    assert prog.get_completed(1, 1) is True
    assert prog.get_completed(1, 2) is False
    assert prog.get_completed(2, 1) is False


def test_show_progress_survives_null_seasons():
    # Trakt drops the seasons breakdown unless extended=progress; parsing must not raise
    # "'NoneType' object is not iterable" (Taxel/PlexTraktSync#2515).
    assert ShowProgress(show={"ids": {"trakt": 1, "slug": "x"}}, seasons=None).get_completed(1, 1) is False


def test_all_shows_progress_survives_null_payload():
    assert AllShowsProgress(None).shows == {}


@pytest.mark.parametrize(
    ("fetch_all", "path", "extended"),
    [
        pytest.param(allwatched, "sync/watched/shows", "progress", id="watched"),
        pytest.param(allcollected, "sync/collection/shows", "metadata", id="collected"),
    ],
)
def test_pagination_aggregates_multiple_pages(monkeypatch, fetch_all, path, extended):
    first_page_size = 100
    calls = []

    def fake_paginate(url, **params):
        calls.append((url, params))
        # Model an aggregated two-page result from trakt.pagination.paginate:
        # a full first page plus one extra show from the final short page.
        return [_show(i) for i in range(first_page_size)] + [_show(1000)]

    monkeypatch.setattr(pytrakt_extensions, "paginate", fake_paginate)

    progress = fetch_all()

    assert calls == [(path, {"extended": extended})]
    assert len(progress.shows) == first_page_size + 1
    assert progress.get_completed(1000, 1, 1) is True
