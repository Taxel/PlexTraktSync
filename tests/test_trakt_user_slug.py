#!/usr/bin/env python3 -m pytest
from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from click import ClickException
from trakt.errors import ForbiddenException, OAuthException, OAuthRefreshException
from trakt.movies import Movie

from plextraktsync.trakt.TraktApi import TraktApi
from plextraktsync.trakt.TraktUserList import TraktUserList

NO_IDS = object()
DISPLAY_NAME = "用户名"


class FakeTraktClient:
    def __init__(self, responses):
        self.responses = responses
        self.urls = []

    def get(self, url, include_headers=False):
        self.urls.append(url)
        path = url.split("?", 1)[0]
        if path not in self.responses:
            raise AssertionError(f"unexpected Trakt request: {url}")
        body = self.responses[path]
        if include_headers:
            return body, {}
        return body


@contextmanager
def trakt_responses(responses):
    client = FakeTraktClient(responses)
    with patch("trakt.decorators.api", return_value=client):
        yield client


def user_payload(ids):
    payload = {"username": DISPLAY_NAME}
    if ids is not NO_IDS:
        payload["ids"] = ids
    return payload


def liked_list(owner):
    return {
        "type": "list",
        "list": {
            "name": "My List",
            "privacy": "private",
            "type": "personal",
            "ids": {"trakt": 55, "slug": "my-list"},
            "user": owner,
        },
    }


@pytest.fixture
def trakt_api():
    with patch("plextraktsync.trakt.TraktApi.factory") as mock_factory:
        mock_factory.session = MagicMock()
        yield TraktApi()


def test_me_username_slug_is_used_for_watched_movies(trakt_api, monkeypatch):
    observed = []

    def fake_paginate(url, api=None, **params):
        observed.append(params["user"])
        return [
            {"movie": {"title": "Arrival", "year": 2016, "ids": {"trakt": 10, "slug": "arrival-2016"}}},
            {"movie": {"title": "Dune", "year": 2021, "ids": {"trakt": 20, "slug": "dune-2021"}}},
        ]

    monkeypatch.setattr("trakt.users.paginate", fake_paginate)
    with trakt_responses({"users/me": user_payload({"slug": "yong-hu"})}):
        assert trakt_api.me.username == "yong-hu"
        assert trakt_api.watched_movies == {10, 20}

    assert observed == ["yong-hu"]


def test_liked_lists_stores_owner_slug(trakt_api):
    owner = user_payload({"slug": "yong-hu"})
    with trakt_responses(
        {
            "users/me": user_payload({"slug": "yong-hu"}),
            "users/likes/lists": [liked_list(owner)],
        }
    ):
        assert trakt_api.liked_lists == [
            {
                "listname": "My List",
                "username": "yong-hu",
                "listid": 55,
                "private": True,
                "list_type": "personal",
            }
        ]


class FakePersonalList:
    def __init__(self, items):
        self.name = "My List"
        self.description = "a description"
        self._items = items

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)


class FakeTraktApi:
    def __init__(self, user_list):
        self.user_list = user_list
        self.personal_lists = []

    @property
    def me(self):
        class Me:
            username = "yong-hu"

        return Me()

    def get_personal_list(self, username, listname):
        self.personal_lists.append((username, listname))
        return self.user_list


def test_private_personal_list_downloads_when_usernames_are_slugs(monkeypatch):
    movies = [Movie("Arrival", year=2016, ids={"trakt": 10, "slug": "arrival-2016"})]
    api = FakeTraktApi(FakePersonalList(movies))
    monkeypatch.setattr("plextraktsync.factory.factory.trakt_api", api, raising=False)
    tl = TraktUserList(trakt_id=1, name="My List", username="yong-hu", is_private=True, list_type="personal")

    description, items = tl.load_items()

    assert api.personal_lists == [("yong-hu", "My List")]
    assert description == "a description"
    assert items == {("movies", 10): 1}


@pytest.mark.parametrize(
    "ids",
    [
        pytest.param(NO_IDS, id="no-ids"),
        pytest.param({"slug": ""}, id="empty-slug"),
        pytest.param({"slug": "别名"}, id="non-ascii-slug"),
    ],
)
def test_unusable_slug_keeps_display_username(trakt_api, ids):
    owner = user_payload(ids)
    with trakt_responses({"users/me": user_payload(ids), "users/likes/lists": [liked_list(owner)]}):
        assert trakt_api.me.username == DISPLAY_NAME
        assert trakt_api.liked_lists[0]["username"] == DISPLAY_NAME


@pytest.mark.parametrize(
    ("error", "match"),
    [
        (ForbiddenException, "Trakt authentication error"),
        (OAuthException, "Trakt authentication error"),
        (OAuthRefreshException, "Unable to refresh token"),
    ],
)
def test_me_auth_errors_raise_click_exception(trakt_api, error, match):
    with (
        patch("trakt.users.User", side_effect=error),
        pytest.raises(ClickException, match=match),
    ):
        _ = trakt_api.me
