import click

from plex_trakt_sync.commands.login import ensure_login
from plex_trakt_sync.factory import factory
from plex_trakt_sync.media import Media
from plex_trakt_sync.plex_api import PlexApi
from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.decorators.measure_time import measure_time
from plex_trakt_sync.trakt_api import TraktApi
from plex_trakt_sync.trakt_list_util import TraktListUtil
from plex_trakt_sync.logging import logger
from plex_trakt_sync.version import git_version_info
from plex_trakt_sync.walker import Walker


def sync_collection(m: Media):
    if not CONFIG['sync']['collection']:
        return

    if m.is_collected:
        return

    logger.info(f"To be added to collection: {m}")
    m.add_to_collection()


def sync_ratings(m: Media):
    if not CONFIG['sync']['ratings']:
        return

    if m.plex_rating is m.trakt_rating:
        return

    # Plex rating takes precedence over Trakt rating
    if m.plex_rating is not None:
        logger.info(f"Rating {m} with {m.plex_rating} on Trakt")
        m.trakt_rate()
    elif m.trakt_rating is not None:
        logger.info(f"Rating {m} with {m.trakt_rating} on Plex")
        m.plex_rate()


def sync_watched(m: Media):
    if not CONFIG['sync']['watched_status']:
        return

    if m.watched_on_plex is m.watched_on_trakt:
        return

    if m.watched_on_plex:
        logger.info(f"Marking as watched in Trakt: {m}")
        m.mark_watched_trakt()
    elif m.watched_on_trakt:
        logger.info(f"Marking as watched in Plex: {m}")
        m.mark_watched_plex()


def sync_all(walker: Walker, trakt: TraktApi, plex: PlexApi):
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

    logger.info(f"Plex Server version: {plex.version}, updated at: {plex.updated_at}")

    for movie in walker.find_movies():
        sync_collection(movie)
        sync_ratings(movie)
        sync_watched(movie)
        # add to plex lists
        listutil.addPlexItemToLists(movie)

    for episode in walker.find_episodes():
        sync_collection(episode)
        sync_watched(episode)

        # add to plex lists
        listutil.addPlexItemToLists(episode)

    with measure_time("Updated plex watchlist"):
        listutil.updatePlexLists(plex)

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
def sync(sync_option: str, library: str, show: str, movie: str, batch_size: int):
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
    w = Walker(plex, mf, movies=movies, shows=tv, progressbar=click.progressbar)

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

    w.walk_details(print=click.echo)

    with measure_time("Completed full sync"):
        sync_all(walker=w, trakt=trakt, plex=plex)
