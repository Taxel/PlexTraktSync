import click
from plex_trakt_sync.main import main


@click.command()
def cli():
    """
    Plex-Trakt-Sync is a two-way-sync between trakt.tv and Plex Media Server
    """

    main()
