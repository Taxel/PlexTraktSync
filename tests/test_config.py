#!/usr/bin/env python3 -m pytest
from os.path import join

import pytest

from plextraktsync.config.Config import Config
from plextraktsync.factory import factory


def test_config_merge():
    config = factory.config

    override = {"root": {"key1": "value1"}}
    config.merge(override, config)
    override = {"root": {"key2": "value2"}}
    config.merge(override, config)
    assert config["root"]["key1"] == "value1"
    assert config["root"]["key2"] == "value2"


def test_config_merge_real():
    from tests.conftest import MOCK_DATA_DIR

    config_file = join(MOCK_DATA_DIR, "673-config.yml")
    config = Config(config_file)

    assert config["sync"]["plex_to_trakt"]["collection"] is False


@pytest.mark.skip(reason="Broken in CI")
def test_sync_config():
    from tests.conftest import MOCK_DATA_DIR

    config_file = join(MOCK_DATA_DIR, "673-config.yml")
    sync_config = Config(config_file).sync

    assert sync_config.plex_to_trakt["collection"] is False


def test_http_config():
    from tests.conftest import MOCK_DATA_DIR

    config = Config()
    config.config_yml = join(MOCK_DATA_DIR, "http_cache-blank.yml")
    assert config.http_cache is not None

    config = Config()
    config.config_yml = join(MOCK_DATA_DIR, "http_cache-empty.yml")
    assert config.http_cache is not None

    config = Config()
    config.config_yml = join(MOCK_DATA_DIR, "http_cache-1-entry.yml")
    cache = config.http_cache
    assert cache is not None
    assert cache.policy["a"] == "b"
