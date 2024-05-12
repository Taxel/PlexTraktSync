#!/usr/bin/env python3 -m pytest
from plextraktsync.sync.plugin import SyncPluginManager


def test_plugin():
    """
    Test that plugin framework initializes
    """
    pm = SyncPluginManager()
    assert pm is not None
