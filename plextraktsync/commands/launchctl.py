import click

from plextraktsync.decorators.cached_property import cached_property


class Plist:
    plist_file = "com.github.plextraktsync.watch.plist"

    def load(self, plist_path: str):
        from os import system

        system(f"launchctl load {plist_path}")

    def unload(self, plist_path: str):
        from os import system
        from os.path import exists

        # Skip if file does not exist.
        if not exists(plist_path):
            return
        system(f"launchctl unload {plist_path}")

    def create(self, plist_path: str):
        from plextraktsync.util.packaging import program_path

        with open(self.plist_default_path, encoding='utf-8') as f:
            contents = "".join(f.readlines())

        def encode(f):
            return f'<string>{f}</string>'

        program = "\n".join(map(encode, program_path().split(' ')))
        contents = contents.replace('<string>plextraktsync</string>', program)
        with open(plist_path, "w+") as fw:
            fw.writelines(contents)

    def remove(self, plist_path: str):
        from os import unlink
        from os.path import exists

        # Skip if file does not exist.
        if not exists(plist_path):
            return
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
    p = Plist()
    p.create(p.plist_path)
    click.echo(f"Created: {p.plist_path}")
    p.load(p.plist_path)
    click.echo(f"Loaded: {p.plist_path}")


@click.command()
def unload():
    """
    Unload the service.
    """
    p = Plist()
    p.unload(p.plist_path)
    click.echo(f"Unloaded: {p.plist_path}")
    p.remove(p.plist_path)
    click.echo(f"Removed: {p.plist_path}")
