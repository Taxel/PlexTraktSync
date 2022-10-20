import click

from plextraktsync.decorators.cached_property import cached_property


class Plist:
    plist_file = "com.github.plextraktsync.watch.plist"

    def create(self, plist_path: str):
        from shutil import copy
        copy(self.plist_default_path, plist_path)

    def remove(self, plist_path: str):
        from os import unlink
        unlink(plist_path)

    @cached_property
    def plist_default_path(self):
        from os.path import join

        from plextraktsync.path import module_path

        return join(module_path, self.plist_file)

    @cached_property
    def plist_path(self):
        from os.path import expanduser

        return expanduser(f'~/Library/LaunchAgents/{self.plist_file}')


@click.command()
def load():
    """
    Load the service.
    """
    pass


@click.command()
def unload():
    """
    Unload the service.
    """
    pass
