import click

from plextraktsync.commands.cache import cache
from plextraktsync.commands.clear_collections import clear_collections
from plextraktsync.commands.info import info
from plextraktsync.commands.inspect import inspect
from plextraktsync.commands.login import login
from plextraktsync.commands.plex_login import plex_login
from plextraktsync.commands.self_update import enable_self_update, self_update
from plextraktsync.commands.sync import sync
from plextraktsync.commands.trakt_login import trakt_login
from plextraktsync.commands.unmatched import unmatched
from plextraktsync.commands.watch import watch
from plextraktsync.commands.webhook import webhook


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
cli.add_command(info)
cli.add_command(inspect)
cli.add_command(login)
cli.add_command(plex_login)
if enable_self_update():
    cli.add_command(self_update)
cli.add_command(sync)
cli.add_command(trakt_login)
cli.add_command(unmatched)
cli.add_command(watch)
cli.add_command(webhook)
