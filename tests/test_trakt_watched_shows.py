#!/usr/bin/env python3 -m pytest
from __future__ import annotations

from unittest.mock import MagicMock, patch

from plextraktsync.pytrakt_extensions import AllShowsProgress
from plextraktsync.trakt.TraktApi import TraktApi


def make_watched_progress(trakt_id: int, slug: str):
    return {
        "aired": 1,
        "completed": False,
        "last_watched_at": None,
        "last_updated_at": None,
        "reset_at": None,
        "type": "show",
        "show": {"ids": {"trakt": trakt_id, "slug": slug}},
        "seasons": [
            {
                "number": 1,
                "episodes": [
                    {"number": 1, "plays": 1, "completed": True},
                ],
            }
        ],
        "hidden_seasons": [],
        "next_episode": 1,
        "last_episode": 1,
        "last_collected_at": None,
    }


def test_watched_shows_reports_episode_completion_from_progress_data():
    with (
        patch("plextraktsync.trakt.TraktApi.factory") as mock_factory,
        patch("plextraktsync.trakt.TraktApi.pytrakt_extensions.allwatched") as mock_allwatched,
    ):
        mock_factory.session = MagicMock()
        mock_allwatched.return_value = AllShowsProgress(
            [
                make_watched_progress(10, "show-one"),
                make_watched_progress(20, "show-two"),
            ]
        )

        trakt_api = TraktApi()
        watched = trakt_api.watched_shows

    assert watched.get_completed(10, 1, 1) is True
    assert watched.get_completed(20, 1, 1) is True
    assert watched.get_completed(10, 1, 2) is False
    assert watched.get_completed(999, 1, 1) is False
