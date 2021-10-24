import click
from tqdm import tqdm

from plex_trakt_sync.commands.login import ensure_login
from plex_trakt_sync.decorators.measure_time import measure_time
from plex_trakt_sync.factory import factory
from plex_trakt_sync.logging import logger
from plex_trakt_sync.plex_api import PlexApi
from plex_trakt_sync.sync import Sync
from plex_trakt_sync.version import git_version_info
from plex_trakt_sync.walker import Walker


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
    "--sync", "sync_option",
    type=click.Choice(["all", "movies", "tv"], case_sensitive=False),
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
def sync(sync_option: str, library: str, show: str, movie: str, batch_size: int, dry_run: bool, no_progress_bar: bool):
    """
    Perform sync between Plex and Trakt
    """

    git_version = git_version_info()
    if git_version:
        logger.info(f"PlexTraktSync [{git_version}]")

    ensure_login()
    CONFIG = factory.config()
    logger.info(f"Syncing with Plex {CONFIG['PLEX_USERNAME']} and Trakt {CONFIG['TRAKT_USERNAME']}")

    movies = sync_option in ["all", "movies"]
    tv = sync_option in ["all", "tv"]

    plex = factory.plex_api()
    trakt = factory.trakt_api(batch_size=batch_size)
    mf = factory.media_factory(batch_size=batch_size)
    pb = factory.progressbar(not no_progress_bar)
    w = Walker(plex=plex, trakt=trakt, mf=mf, movies=movies, shows=tv, progressbar=pb)

    if library:
        logger.info(f"Filtering Library: {library}")
        w.add_library(library)
    if show:
        w.add_show(show)
        logger.info(f"Syncing Show: {show}")
    if movie:
        w.add_movie(movie)
        logger.info(f"Syncing Movie: {movie}")

    if not w.is_valid():
        click.echo("Nothing to sync, this is likely due conflicting options given.")
        return

    if dry_run:
        print("Enabled dry-run mode: not making actual changes")
    w.walk_details(print=tqdm.write)

    with measure_time("Completed full sync"):
        sync_all(walker=w, plex=plex, runner=factory.sync(), dry_run=dry_run)
