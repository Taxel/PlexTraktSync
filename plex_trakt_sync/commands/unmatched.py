import click

from plex_trakt_sync.commands.login import ensure_login
from plex_trakt_sync.media import MediaFactory
from plex_trakt_sync.plex_api import PlexApi
from plex_trakt_sync.plex_server import get_plex_server
from plex_trakt_sync.trakt_api import TraktApi
from plex_trakt_sync.walker import Walker


@click.command()
def unmatched():
    """
    List media that has no match in Plex
    """

    ensure_login()
    server = get_plex_server()
    plex = PlexApi(server)
    trakt = TraktApi()
    mf = MediaFactory(plex, trakt)
    walker = Walker(plex, mf, progressbar=click.progressbar)

    if not walker.is_valid():
        click.echo("Nothing to scan, this is likely due conflicting options given.")
        return

    walker.walk_details(print=click.echo)

    for movie in walker.find_movies():
        print(f"{movie}")
