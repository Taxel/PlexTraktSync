from typing import List

import click
from click import ClickException
from tqdm import tqdm

from plextraktsync.commands.login import ensure_login
from plextraktsync.decorators.measure_time import measure_time
from plextraktsync.factory import factory
from plextraktsync.logging import logger
from plextraktsync.plex_api import PlexApi
from plextraktsync.sync import Sync
from plextraktsync.version import version
from plextraktsync.walker import Walker


def sync_all(walker: Walker, plex: PlexApi, runner: Sync, dry_run: bool):
    click.echo(f"Plex Server version: {plex.version}, updated at: {plex.updated_at}")
    click.echo(f"Server has {len(plex.library_sections)} libraries: {plex.library_section_names}")

    runner.sync(walker, dry_run=dry_run)


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
    CONFIG = factory.config()
    logger.info(f"Syncing with Plex {CONFIG['PLEX_USERNAME']} and Trakt {CONFIG['TRAKT_USERNAME']}")

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

    if dry_run:
        print("Enabled dry-run mode: not making actual changes")
    w.print_plan(print=tqdm.write)

    plex = factory.plex_api()
    with measure_time("Completed full sync"):
        try:
            sync_all(walker=w, plex=plex, runner=factory.sync(), dry_run=config.dry_run)
        except RuntimeError as e:
            raise ClickException(str(e))
