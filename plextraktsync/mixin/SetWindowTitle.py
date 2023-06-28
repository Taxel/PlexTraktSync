from plextraktsync.decorators.cached_property import cached_property


class SetWindowTitle:
    @cached_property
    def console(self):
        from plextraktsync.factory import factory

        return factory.console

    def set_window_title(self, title: str):
        self.console.set_window_title(f"PlexTraktSync: {title}")
