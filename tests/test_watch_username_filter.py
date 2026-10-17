#!/usr/bin/env python3 -m pytest
from __future__ import annotations

import pytest

from plextraktsync.watch.WatchStateUpdater import WatchStateUpdater


class FakeAccount:
    """Stands in for MyPlexAccount, which would reach plex.tv."""

    def __init__(self, username="from-plex-tv"):
        self.username = username


class FakePlexApi:
    def __init__(self, has_sessions=True, username="from-plex-tv"):
        self._has_sessions = has_sessions
        self._username = username
        self.account_calls = 0

    def has_sessions(self):
        return self._has_sessions

    @property
    def account(self):
        self.account_calls += 1

        return FakeAccount(self._username)


def make_updater(plex_username, has_sessions=True, account_username="from-plex-tv"):
    config = {
        "watch": {
            "username_filter": True,
            "add_collection": False,
            "remove_collection": False,
            "ignore_clients": None,
        },
        "PLEX_USERNAME": plex_username,
        "PLEX_ACCOUNT_TOKEN": None,
    }
    plex = FakePlexApi(has_sessions=has_sessions, username=account_username)
    updater = WatchStateUpdater(plex=plex, trakt=None, mf=None, config=config)

    return updater, plex


@pytest.mark.parametrize(
    "plex_username,expected",
    [
        ("myusername", "myusername"),
        # An e-mail never matches a session username, so it is not usable here
        ("user@example.com", None),
        ("", None),
        (None, None),
    ],
)
def test_configured_username(plex_username, expected):
    updater, _ = make_updater(plex_username)

    assert updater.configured_username == expected


def test_username_filter_prefers_config_over_plex_tv():
    updater, plex = make_updater("myusername", account_username="from-plex-tv")

    assert updater.username_filter == "myusername"
    # The whole point: no MyPlexAccount is constructed, so plex.tv is untouched
    assert plex.account_calls == 0


def test_username_filter_falls_back_to_plex_tv_when_config_unusable():
    updater, plex = make_updater("user@example.com", account_username="from-plex-tv")

    assert updater.username_filter == "from-plex-tv"
    assert plex.account_calls == 1


def test_username_filter_is_cached():
    updater, plex = make_updater("myusername")

    assert updater.username_filter == "myusername"
    assert updater.username_filter == "myusername"
    assert updater.username_filter_resolved is True
    assert plex.account_calls == 0


def test_username_filter_not_resolved_without_sessions():
    """Owner token with no session access must fail closed, as before."""
    updater, plex = make_updater("myusername", has_sessions=False)

    assert updater.username_filter is None
    assert updater.username_filter_resolved is False
    assert plex.account_calls == 0


def test_can_scrobble_skips_other_users():
    updater, _ = make_updater("myusername")
    updater.sessions = {"1": "myusername", "2": "someone-else"}

    class Event:
        client_identifier = "client"

        def __init__(self, session_key):
            self.session_key = session_key

    assert updater.can_scrobble(Event("1")) is True
    assert updater.can_scrobble(Event("2")) is False
