import click

from plex_trakt_sync.requests_cache import requests_cache
from plex_trakt_sync.plex_server import get_plex_server
from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.decorators import measure_time
from plex_trakt_sync.main import process_show_section
from plex_trakt_sync.plex_api import PlexApi
from plex_trakt_sync.trakt_api import TraktApi
from plex_trakt_sync.trakt_list_util import TraktListUtil
from plex_trakt_sync.logging import logging


def sync_collection(pm, tm, trakt: TraktApi, trakt_movie_collection):
    if not CONFIG['sync']['collection']:
        return

    if tm.trakt in trakt_movie_collection:
        return

    logging.info(f"Add to Trakt Collection: {pm}")
    trakt.add_to_collection(tm)


def sync_ratings(pm, tm, plex: PlexApi, trakt: TraktApi):
    if not CONFIG['sync']['ratings']:
        return

    trakt_rating = trakt.rating(tm)
    plex_rating = pm.rating
    if plex_rating is trakt_rating:
        return

    # Plex rating takes precedence over Trakt rating
    if plex_rating is not None:
        logging.info(f"Rating {pm} with {plex_rating} on Trakt")
        trakt.rate(tm, plex_rating)
    elif trakt_rating is not None:
        logging.info(f"Rating {pm} with {trakt_rating} on Plex")
        plex.rate(pm.item, trakt_rating)


def sync_watched(pm, tm, plex: PlexApi, trakt: TraktApi, trakt_watched_movies):
    if not CONFIG['sync']['watched_status']:
        return

    watched_on_plex = pm.item.isWatched
    watched_on_trakt = tm.trakt in trakt_watched_movies
    if watched_on_plex is watched_on_trakt:
        return

    # if watch status is not synced
    # send watched status from plex to trakt
    if watched_on_plex:
        logging.info(f"Marking as watched on Trakt: {pm}")
        trakt.mark_watched(tm, pm.seen_date)
    # set watched status if movie is watched on Trakt
    elif watched_on_trakt:
        logging.info(f"Marking as watched in Plex: {pm}")
        plex.mark_watched(pm.item)


def sync_movies(plex, trakt):
    for section in plex.movie_sections:
        with measure_time(f"Processing section {section.title}"):
            for pm in section.items():
                if not pm.provider:
                    logging.error(f'Movie [{pm}]: Unrecognized GUID {pm.guid}')
                    continue

                tm = trakt.find_movie(pm)
                if tm is None:
                    logging.warning(f"Movie [{pm})]: Not found from Trakt. Skipping")
                    continue

                yield pm, tm


def sync_all(movies=True, tv=True):
    with requests_cache.disabled():
        server = get_plex_server()
    listutil = TraktListUtil()
    plex = PlexApi(server)
    trakt = TraktApi()

    with measure_time("Loaded Trakt lists"):
        trakt_watched_movies = trakt.watched_movies
        trakt_watched_shows = trakt.watched_shows
        trakt_movie_collection = trakt.movie_collection_set
        trakt_ratings = trakt.ratings
        trakt_watchlist_movies = trakt.watchlist_movies
        trakt_liked_lists = trakt.liked_lists

    if trakt_watchlist_movies:
        listutil.addList(None, "Trakt Watchlist", traktid_list=trakt_watchlist_movies)

    for lst in trakt_liked_lists:
        listutil.addList(lst['username'], lst['listname'])

    with requests_cache.disabled():
        logging.info("Server version {} updated at: {}".format(server.version, server.updatedAt))
        logging.info("Recently added: {}".format(server.library.recentlyAdded()[:5]))

    if movies:
        for pm, tm in sync_movies(plex, trakt):
            sync_collection(pm, tm, trakt, trakt_movie_collection)
            sync_ratings(pm, tm, plex, trakt)
            sync_watched(pm, tm, plex, trakt, trakt_watched_movies)

    if tv:
        for section in plex.show_sections:
            with measure_time("Processing section %s" % section.title):
                process_show_section(section, trakt_watched_shows, listutil)

    with measure_time("Updated plex watchlist"):
        listutil.updatePlexLists(server)


@click.command()
@click.option(
    "--sync", "sync_option",
    type=click.Choice(["all", "movies", "tv"], case_sensitive=False),
    default="all",
    show_default=True, help="Specify what to sync"
)
def sync(sync_option: str):
    """
    Perform sync between Plex and Trakt
    """

    movies = sync_option in ["all", "movies"]
    tv = sync_option in ["all", "tv"]
    if not movies and not tv:
        click.echo("Nothing to sync!")
        return

    logging.info(f"Syncing with Plex {CONFIG['PLEX_USERNAME']} and Trakt {CONFIG['PLEX_USERNAME']}")
    logging.info(f"Syncing TV={tv}, Movies={movies}")

    with measure_time("Completed full sync"):
        sync_all(movies=movies, tv=tv)
