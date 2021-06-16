import json
from os.path import dirname, join as join_path
from typing import Union

from trakt.tv import TVShow

from plex_trakt_sync.factory import Factory

MOCK_DATA_DIR = join_path(dirname(__file__), "mock_data")
factory = Factory()


def load_mock(name: str):
    filename = join_path(MOCK_DATA_DIR, name)
    with open(filename, encoding='utf-8') as f:
        return json.load(f)


def make(cls=None, **kwargs) -> Union[TVShow]:
    cls = cls if cls is not None else "object"
    # https://stackoverflow.com/a/2827726/2314626
    return type(cls, (object,), kwargs)
