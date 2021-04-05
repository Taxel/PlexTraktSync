import click
from plex_trakt_sync.logging import logging
from plex_trakt_sync.trakt_api import TraktApi


@click.command()
@click.option('--confirm', is_flag=True, help='Confirm the dangerous action')
def clear_collections(confirm):
    """
    Clear Movies and Shows collections in Trakt
    """

    if not confirm:
        click.echo('You need to pass --confirm option to proceed')
        return

    trakt = TraktApi()

    for movie in trakt.movie_collection:
        logging.info(f"Deleting: {movie}")
        trakt.remove_from_library(movie)

    for show in trakt.show_collection:
        logging.info(f"Deleting: {show}")
        trakt.remove_from_library(show)
