from __future__ import annotations

import contextlib
import json
from os import environ
from os.path import dirname
from os.path import join as join_path

from trakt.tv import TVShow

from plextraktsync.factory import Factory

TESTS_DIR = dirname(__file__)
MOCK_DATA_DIR = join_path(TESTS_DIR, "mock_data")
factory = Factory()

# Patch config to use separate config for tests
config = factory.config
config.config_file = join_path(TESTS_DIR, "config.json")
config.env_file = join_path(TESTS_DIR, ".env")

# Delete environment to ensure consistent tests
for key in config.env_keys:
    with contextlib.suppress(KeyError):
        del environ[key]


def load_mock(name: str):
    filename = join_path(MOCK_DATA_DIR, name)
    with open(filename, encoding="utf-8") as f:
        return json.load(f)


def make(cls=None, **kwargs) -> TVShow:
    cls = cls if cls is not None else "object"
    # https://stackoverflow.com/a/2827726/2314626
    return type(cls, (object,), kwargs)
