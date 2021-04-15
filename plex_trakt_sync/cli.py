import click
from plex_trakt_sync.commands.clear_collections import clear_collections
from plex_trakt_sync.commands.sync import sync
from plex_trakt_sync.commands.inspect import inspect
from plex_trakt_sync.commands.watch import watch


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """
    Plex-Trakt-Sync is a two-way-sync between trakt.tv and Plex Media Server
    """
    if not ctx.invoked_subcommand:
        sync()


cli.add_command(sync)
cli.add_command(clear_collections)
cli.add_command(inspect)
cli.add_command(watch)
