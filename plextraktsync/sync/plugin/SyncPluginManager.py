from __future__ import annotations

from functools import cached_property

import pluggy


class SyncPluginManager:
    @cached_property
    def pm(self):
        from .SyncPluginInterface import SyncPluginInterface

        pm = pluggy.PluginManager("PlexTraktSync")
        pm.add_hookspecs(SyncPluginInterface)

        return pm

    @cached_property
    def hook(self):
        return self.pm.hook
