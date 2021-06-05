import click

from plex_trakt_sync.commands.plex_login import has_plex_token, plex_login
from plex_trakt_sync.commands.trakt_login import has_trakt_token, trakt_login


def ensure_login():
    if not has_plex_token():
        plex_login()
    if not has_trakt_token():
        trakt_login()


@click.command()
def login():
    """
    Log in to Plex and Trakt if needed
    """
    ensure_login()
