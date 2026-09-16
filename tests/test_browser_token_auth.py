from __future__ import annotations

import json
import time

import pytest
from click import ClickException
from requests import Request, Response, Session
from requests.adapters import BaseAdapter
from trakt.api import HttpClient

from plextraktsync.trakt.BrowserTokenAuth import BrowserTokenAuth


class Adapter(BaseAdapter):
    def __init__(self, status=200):
        self.status = status
        self.requests = []

    def send(self, request, **kwargs):
        self.requests.append(request)
        response = Response()
        response.status_code = self.status
        response._content = b'{}'
        response.request = request
        return response

    def close(self):
        pass


def test_real_client_reloads_token_and_sends_writes(tmp_path):
    path = tmp_path / 'token.json'
    session = Session()
    adapter = Adapter()
    session.mount('https://', adapter)
    client = HttpClient('https://api.trakt.tv/', session)
    client.auth = BrowserTokenAuth(path)
    for token in ('first', 'second'):
        path.write_text(json.dumps(dict(access_token=token, client_id='key')))
        client.post('sync/history', {'movies': []})
        assert adapter.requests[-1].headers['Authorization'] == 'Bearer ' + token
        assert adapter.requests[-1].headers['trakt-api-key'] == 'key'
    assert len(adapter.requests) == 2


@pytest.mark.parametrize('data', [{}, [], {'access_token': 'secret\nbad', 'client_id': 'key'},
    {'access_token': 'secret', 'client_id': 'key', 'expires_at': time.time()-1}])
def test_invalid_or_expired(tmp_path, data):
    path = tmp_path / 'token.json'
    path.write_text(json.dumps(data))
    with pytest.raises(ClickException) as error:
        BrowserTokenAuth(path).read()
    assert 'secret' not in str(error.value)


def test_unexpected_host(tmp_path):
    auth = BrowserTokenAuth(tmp_path / 'missing')
    with pytest.raises(ClickException, match='unexpected endpoint'):
        Request('GET', 'https://example.com', auth=auth).prepare()


def test_401_does_not_replay(tmp_path):
    path = tmp_path / 'token.json'
    path.write_text(json.dumps(dict(access_token='secret', client_id='key')))
    session = Session()
    adapter = Adapter(401)
    session.mount('https://', adapter)
    with pytest.raises(ClickException, match='not replayed'):
        session.get('https://api.trakt.tv/users/settings', auth=BrowserTokenAuth(path))
    assert len(adapter.requests) == 1


def test_api_installs_browser_auth_and_skips_oauth(tmp_path):
    from unittest.mock import MagicMock, patch

    import trakt.core

    from plextraktsync.commands.trakt_login import login
    from plextraktsync.trakt.TraktApi import TraktApi

    path = tmp_path / 'token.json'
    path.write_text(json.dumps(dict(access_token='secret', client_id='key')))
    config = {'TRAKT_BROWSER_TOKEN_FILE': str(path)}
    trakt.core.api.cache_clear()
    try:
        with patch('plextraktsync.trakt.TraktApi.factory') as factory:
            factory.config = config
            factory.session = Session()
            api = TraktApi()
            assert isinstance(trakt.core.api().auth, BrowserTokenAuth)
        with patch('plextraktsync.commands.trakt_login.factory') as factory, \
             patch('plextraktsync.commands.trakt_login.trakt_authenticate') as oauth:
            api.me = MagicMock(username='test-user')
            factory.trakt_api = api
            factory.config = MagicMock()
            login()
            oauth.assert_not_called()
            factory.config.save.assert_called_once()
    finally:
        trakt.core.api.cache_clear()
