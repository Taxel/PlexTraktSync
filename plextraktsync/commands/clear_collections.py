import click

from plextraktsync.factory import factory
from plextraktsync.logging import logger


@click.command()
@click.option('--confirm', is_flag=True, help='Confirm the dangerous action')
@click.option('--dry-run', is_flag=True, help='Do not perform delete actions')
def clear_collections(confirm, dry_run):
    """
    Clear Movies and Shows collections in Trakt
    """

    if not confirm and not dry_run:
        click.echo('You need to pass --confirm or --dry-run option to proceed')
        return

    trakt = factory.trakt_api()

    for movie in trakt.movie_collection:
        logger.info(f"Deleting: {movie}")
        if not dry_run:
            trakt.remove_from_library(movie)

    for show in trakt.show_collection:
        logger.info(f"Deleting: {show}")
        if not dry_run:
            trakt.remove_from_library(show)
