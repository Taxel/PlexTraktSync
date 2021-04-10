import click
from plexapi.server import PlexServer
from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.plex_api import PlexApi


@click.command()
def plex_login():
    """
    Log in to Plex Account
    """
