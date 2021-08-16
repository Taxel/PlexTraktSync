import click
from tqdm import tqdm

from plex_trakt_sync.commands.login import ensure_login
from plex_trakt_sync.decorators.measure_time import measure_time
from plex_trakt_sync.factory import factory
from plex_trakt_sync.logging import logger
from plex_trakt_sync.plex_api import PlexApi
from plex_trakt_sync.sync import Sync
from plex_trakt_sync.trakt_api import TraktApi
from plex_trakt_sync.trakt_list_util import TraktListUtil
from plex_trakt_sync.version import git_version_info
from plex_trakt_sync.walker import Walker

CONFIG = factory.config()


def sync_all(walker: Walker, trakt: TraktApi, plex: PlexApi, dry_run: bool):
    listutil = TraktListUtil()

    with measure_time("Loaded Trakt lists"):
        trakt_watched_movies = trakt.watched_movies
        trakt_watched_shows = trakt.watched_shows
        trakt_movie_collection = trakt.movie_collection_set
        trakt_ratings = trakt.ratings
        trakt_watchlist_movies = trakt.watchlist_movies
        trakt_liked_lists = trakt.liked_lists

    if trakt_watchlist_movies:
        listutil.addList(None, "Trakt Watchlist", trakt_list=trakt_watchlist_movies)

    for lst in trakt_liked_lists:
        listutil.addList(lst['username'], lst['listname'])

    click.echo(f"Plex Server version: {plex.version}, updated at: {plex.updated_at}")
    # Load sections, this will attempt to connect to Plex
    click.echo(f"Server has {len(plex.library_sections)} libraries: {plex.library_section_names}")

    runner = Sync(CONFIG)
    runner.sync(walker, listutil, dry_run=dry_run)

    if not dry_run:
        with measure_time("Updated plex watchlist"):
            listutil.updatePlexLists(plex)

    if not dry_run:
        trakt.flush()


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
    logger.info(f"Syncing with Plex {CONFIG['PLEX_USERNAME']} and Trakt {CONFIG['TRAKT_USERNAME']}")

    movies = sync_option in ["all", "movies"]
    tv = sync_option in ["all", "tv"]

    plex = factory.plex_api()
    trakt = factory.trakt_api(batch_size=batch_size)
    mf = factory.media_factory(batch_size=batch_size)
    pb = factory.progressbar(not no_progress_bar)
    w = Walker(plex, mf, movies=movies, shows=tv, progressbar=pb)

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
        sync_all(walker=w, trakt=trakt, plex=plex, dry_run=dry_run)
