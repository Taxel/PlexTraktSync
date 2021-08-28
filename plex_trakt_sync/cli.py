import click

from plex_trakt_sync.commands.cache import cache
from plex_trakt_sync.commands.clear_collections import clear_collections
from plex_trakt_sync.commands.inspect import inspect
from plex_trakt_sync.commands.login import login
from plex_trakt_sync.commands.plex_login import plex_login
from plex_trakt_sync.commands.sync import sync
from plex_trakt_sync.commands.trakt_login import trakt_login
from plex_trakt_sync.commands.unmatched import unmatched
from plex_trakt_sync.commands.version import version
from plex_trakt_sync.commands.watch import watch
from plex_trakt_sync.commands.webhook import webhook


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """
    Plex-Trakt-Sync is a two-way-sync between trakt.tv and Plex Media Server
    """
    if not ctx.invoked_subcommand:
        sync()


cli.add_command(cache)
cli.add_command(clear_collections)
cli.add_command(inspect)
cli.add_command(login)
cli.add_command(plex_login)
cli.add_command(sync)
cli.add_command(trakt_login)
cli.add_command(unmatched)
cli.add_command(version)
cli.add_command(watch)
cli.add_command(webhook)
