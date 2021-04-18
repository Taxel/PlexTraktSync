#!/usr/bin/env python3 -m pytest
from plex_trakt_sync.version import git_version_info


def test_version():
    v = git_version_info()

    assert type(v) == str
