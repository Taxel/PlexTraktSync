import click

from plextraktsync.commands.plex_login import (has_plex_token,
                                               plex_login_autoconfig)
from plextraktsync.commands.trakt_login import (has_trakt_token,
                                                trakt_login_autoconfig)
from plextraktsync.style import highlight, success


def ensure_login():
    if not has_plex_token():
        plex_login_autoconfig()

    if not has_trakt_token():
        trakt_login_autoconfig()


def login():
    click.echo(highlight("Checking Plex and Trakt login credentials existence"))
    click.echo("")
    click.echo("It will not test if the credentials are valid, only that they are present.")
    click.echo('If you need to re-login use "plex-login" or "trakt-login" commands respectively.')
    click.echo("")
    ensure_login()
    click.echo(success("Done!"))
