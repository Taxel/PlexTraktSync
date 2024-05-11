#!/usr/bin/env python3 -m pytest
from plextraktsync.factory import factory


def test_plugin():
    """
    Test that plugin framework initializes
    """
    sync = factory.sync
    assert sync is not None
    pm = sync.pm
    assert pm is not None
