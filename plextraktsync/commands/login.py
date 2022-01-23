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
    click.echo(highlight("Checking Plex and Trakt logins"))
    ensure_login()
    click.echo(success("Success!"))
