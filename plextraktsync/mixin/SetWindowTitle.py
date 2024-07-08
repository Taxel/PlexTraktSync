from __future__ import annotations

from functools import cached_property


class SetWindowTitle:
    @cached_property
    def console(self):
        from plextraktsync.factory import factory

        return factory.console

    def clear_window_title(self):
        self.console.set_window_title("PlexTraktSync")

    def set_window_title(self, title: str):
        self.console.set_window_title(f"PlexTraktSync: {title}")
