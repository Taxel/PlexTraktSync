#!/usr/bin/env python3 -m pytest
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from plextraktsync.config.PlexServerConfig import PlexServerConfig
from plextraktsync.config.SyncConfig import SyncConfig
from plextraktsync.sync.SyncYamtrackPlugin import SyncYamtrackPlugin
from plextraktsync.yamtrack.YamtrackApi import YamtrackApi
from tests.conftest import factory, make


class DummyResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload
        self.text = ""
        self.content = b"" if payload is None else b"x"

    def json(self):
        return self._payload


def test_config_serialize_omits_yamtrack_token():
    config = factory.config
    config["YAMTRACK_TOKEN"] = "secret-token"

    assert "YAMTRACK_TOKEN" not in config.serialize()


def test_sync_config_needs_library_walk_when_yamtrack_enabled():
    config = factory.config
    config["sync"]["yamtrack"] = {"enabled": True, "url": "https://yamtrack.example", "timeout": 30}
    config["YAMTRACK_TOKEN"] = "token"
    sync = SyncConfig(config, PlexServerConfig(name="default", token="token", urls=["http://plex"], config={}))

    assert sync.sync_yamtrack_history is True
    assert sync.need_library_walk is True


def test_yamtrack_api_movie_requests():
    session = MagicMock()
    session.request.side_effect = [
        DummyResponse(payload={"pagination": {"next": None}, "results": [{"end_date": "2025-01-01T20:00:00Z"}]}),
        DummyResponse(status_code=201, payload={"ok": True}),
    ]
    api = YamtrackApi(
        config={"enabled": True, "url": "https://yamtrack.example", "timeout": 30, "token": "token"},
        session=session,
    )

    history = api.movie_history(123)
    api.add_movie_watch(123, datetime(2025, 3, 5, 22, 0, tzinfo=timezone.utc))

    assert history == [{"end_date": "2025-01-01T20:00:00Z"}]
    get_call = session.request.call_args_list[0]
    post_call = session.request.call_args_list[1]
    assert get_call.kwargs["url"] == "https://yamtrack.example/api/v1/media/movie/tmdb/123/history/"
    assert get_call.kwargs["headers"]["Authorization"] == "******"
    assert post_call.kwargs["url"] == "https://yamtrack.example/api/v1/media/movie/"
    assert post_call.kwargs["json"] == {
        "source": "tmdb",
        "media_id": "123",
        "status": 3,
        "end_date": "2025-03-05T22:00:00Z",
    }


def test_sync_yamtrack_plugin_posts_only_missing_history():
    yamtrack = MagicMock()
    yamtrack.movie_history.return_value = [{"end_date": "2025-01-01T20:00:00Z"}]
    yamtrack.episode_history.return_value = [{"end_date": "2025-01-01T20:00:00Z"}]
    yamtrack.history_keys.side_effect = lambda entries: {entry["end_date"] for entry in entries}
    yamtrack.normalize_datetime.side_effect = lambda dt: dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    plugin = SyncYamtrackPlugin(
        config=make(sync_yamtrack_history=True),
        yamtrack=yamtrack,
    )

    movie = make(
        title_link="Movie",
        is_movie=True,
        is_episode=False,
        trakt=make(ids={"ids": {"tmdb": 101}}),
        season_number=None,
        episode_number=None,
        plex_history=lambda: [
            make(viewedAt=datetime(2025, 1, 1, 20, 0, tzinfo=timezone.utc)),
            make(viewedAt=datetime(2025, 3, 5, 22, 0, tzinfo=timezone.utc)),
        ],
    )
    episode = make(
        title_link="Episode",
        is_movie=False,
        is_episode=True,
        trakt=make(ids={"ids": {"tmdb": 999}}),
        show=make(trakt=make(ids={"ids": {"tmdb": 202}})),
        season_number=1,
        episode_number=2,
        plex_history=lambda: [
            make(viewedAt=datetime(2025, 1, 1, 20, 0, tzinfo=timezone.utc)),
            make(viewedAt=datetime(2025, 2, 1, 20, 0, tzinfo=timezone.utc)),
        ],
    )

    import asyncio

    asyncio.run(plugin.sync_history(movie, dry_run=False))
    asyncio.run(plugin.sync_history(episode, dry_run=False))

    yamtrack.add_movie_watch.assert_called_once_with(101, datetime(2025, 3, 5, 22, 0, tzinfo=timezone.utc))
    yamtrack.add_episode_watch.assert_called_once_with(202, 1, 2, datetime(2025, 2, 1, 20, 0, tzinfo=timezone.utc))
