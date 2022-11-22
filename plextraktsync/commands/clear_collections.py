import click

from plextraktsync.factory import factory, logger


def clear_collections(confirm, dry_run):
    if not confirm and not dry_run:
        click.echo("You need to pass --confirm or --dry-run option to proceed")
        return

    trakt = factory.trakt_api

    for movie in trakt.movie_collection:
        logger.info(f"Deleting: {movie}")
        if not dry_run:
            trakt.remove_from_library(movie)

    for show in trakt.show_collection:
        logger.info(f"Deleting: {show}")
        if not dry_run:
            trakt.remove_from_library(show)
