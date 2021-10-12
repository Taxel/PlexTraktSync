import click

from plex_trakt_sync.commands.plex_login import has_plex_token, plex_login_autoconfig
from plex_trakt_sync.commands.trakt_login import has_trakt_token, trakt_login_autoconfig


def ensure_login():
    if not has_plex_token():
        plex_login_autoconfig()
    if not has_trakt_token():
        trakt_login_autoconfig()


@click.command()
def login():
    """
    Log in to Plex and Trakt if needed
    """
    ensure_login()
