from typing import List

import click
from click import ClickException
from tqdm import tqdm

from plextraktsync.commands.login import ensure_login
from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.factory import factory
from plextraktsync.logging import logger
from plextraktsync.version import version


@click.command()
@click.option(
    "--library",
    help="Specify Library to use"
)
@click.option(
    "--show", "show",
    type=str,
    show_default=True, help="Sync specific show only"
)
@click.option(
    "--movie", "movie",
    type=str,
    show_default=True, help="Sync specific movie only"
)
@click.option(
    "--id", "ids",
    type=str,
    multiple=True,
    show_default=True, help="Sync specific item only"
)
@click.option(
    "--sync", "sync_option",
    type=click.Choice(["all", "movies", "tv", "shows"], case_sensitive=False),
    default="all",
    show_default=True, help="Specify what to sync"
)
@click.option(
    "--batch-size", "batch_size",
    type=int,
    default=1, show_default=True,
    help="Batch size for collection submit queue"
)
@click.option(
    "--dry-run", "dry_run",
    type=bool,
    default=False,
    is_flag=True,
    help="Dry run: Do not make changes"
)
@click.option(
    "--no-progress-bar", "no_progress_bar",
    type=bool,
    default=False,
    is_flag=True,
    help="Don't output progress bars"
)
def sync(
        sync_option: str,
        library: str,
        show: str,
        movie: str,
        ids: List[str],
        batch_size: int,
        dry_run: bool,
        no_progress_bar: bool,
):
    """
    Perform sync between Plex and Trakt
    """

    logger.info(f"PlexTraktSync [{version()}]")
    ensure_login()

    movies = sync_option in ["all", "movies"]
    shows = sync_option in ["all", "tv", "shows"]

    config = factory.run_config().update(batch_size=batch_size, dry_run=dry_run, progressbar=not no_progress_bar)
    wc = factory.walk_config().update(movies=movies, shows=shows)
    w = factory.walker()

    if ids:
        for id in ids:
            wc.add_id(id)
    if library:
        wc.add_library(library)
    if show:
        wc.add_show(show)
    if movie:
        wc.add_movie(movie)

    if not wc.is_valid():
        click.echo("Nothing to sync, this is likely due conflicting options given.")
        return

    try:
        w.print_plan(print=tqdm.write)
    except RuntimeError as e:
        raise ClickException(str(e))

    if dry_run:
        print("Enabled dry-run mode: not making actual changes")

    with measure_time("Completed full sync"):
        try:
            runner = factory.sync()
            runner.sync(walker=w, dry_run=config.dry_run)
        except RuntimeError as e:
            raise ClickException(str(e))
