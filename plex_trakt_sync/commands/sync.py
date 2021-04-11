import click
from plexapi.exceptions import NotFound

from plex_trakt_sync.requests_cache import requests_cache
from plex_trakt_sync.plex_server import get_plex_server
from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.decorators import measure_time
from plex_trakt_sync.plex_api import PlexApi, PlexLibraryItem
from plex_trakt_sync.trakt_api import TraktApi
from plex_trakt_sync.trakt_list_util import TraktListUtil
from plex_trakt_sync.logging import logger


def sync_collection(pm, tm, trakt: TraktApi, trakt_movie_collection):
    if not CONFIG['sync']['collection']:
        return

    if tm.trakt in trakt_movie_collection:
        return

    logger.info(f"Add to Trakt Collection: {pm}")
    trakt.add_to_collection(tm, pm)


def sync_show_collection(pm, tm, pe, te, trakt: TraktApi):
    if not CONFIG['sync']['collection']:
        return

    collected = trakt.collected(tm)
    is_collected = collected.get_completed(pe.seasonNumber, pe.index)
    if is_collected:
        return

    logger.info(f"Add to Trakt Collection: {pm} S{pe.seasonNumber:02}E{pe.index:02}")
    trakt.add_to_collection(te.instance, pe)


def sync_ratings(pm, tm, plex: PlexApi, trakt: TraktApi):
    if not CONFIG['sync']['ratings']:
        return

    trakt_rating = trakt.rating(tm)
    plex_rating = pm.rating
    if plex_rating is trakt_rating:
        return

    # Plex rating takes precedence over Trakt rating
    if plex_rating is not None:
        logger.info(f"Rating {pm} with {plex_rating} on Trakt")
        trakt.rate(tm, plex_rating)
    elif trakt_rating is not None:
        logger.info(f"Rating {pm} with {trakt_rating} on Plex")
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
        logger.info(f"Marking as watched on Trakt: {pm}")
        trakt.mark_watched(tm, pm.seen_date)
    # set watched status if movie is watched on Trakt
    elif watched_on_trakt:
        logger.info(f"Marking as watched in Plex: {pm}")
        plex.mark_watched(pm.item)


def sync_show_watched(pm, tm, pe, te, trakt_watched_shows, plex: PlexApi, trakt: TraktApi):
    if not CONFIG['sync']['watched_status']:
        return

    watched_on_plex = pe.isWatched
    watched_on_trakt = trakt_watched_shows.get_completed(tm.trakt, pe.seasonNumber, pe.index)

    if watched_on_plex == watched_on_trakt:
        return

    if watched_on_plex:
        logger.info(f"Marking as watched in Trakt: {pm} S{pe.seasonNumber:02}E{pe.index:02}")
        m = PlexLibraryItem(pe)
        trakt.mark_watched(te.instance, m.seen_date)
    elif watched_on_trakt:
        logger.info(f"Marking as watched in Plex: {pm} S{pe.seasonNumber:02}E{pe.index:02}")
        plex.mark_watched(pe)


def for_each_pair(sections, trakt: TraktApi):
    for section in sections:
        label = f"Processing {section.title}"
        with measure_time(label):
            pb = click.progressbar(section.items(), length=len(section), show_pos=True, label=label)
            with pb as items:
                for pm in items:
                    try:
                        provider = pm.provider
                    except NotFound as e:
                        logger.error(f"Skipping {pm}: {e}")
                        continue

                    if provider in ["local", "none", "agents.none"]:
                        continue

                    if provider not in ["imdb", "tmdb", "tvdb"]:
                        logger.error(
                            f"{pm}: Unable to parse a valid provider from guid:'{pm.guid}', guids:{pm.guids}"
                        )
                        continue

                    tm = trakt.find_movie(pm)
                    if tm is None:
                        logger.warning(f"[{pm})]: Not found on Trakt. Skipping")
                        continue

                    yield pm, tm


def for_each_episode(sections, trakt: TraktApi):
    for pm, tm in for_each_pair(sections, trakt):
        lookup = trakt.lookup(tm)

        # loop over episodes in plex db
        for pe in pm.item.episodes():
            try:
                te = lookup[pe.seasonNumber][pe.index]
            except KeyError:
                try:
                    logger.warning(f"Show [{pm}: Key not found: S{pe.seasonNumber:02}E{pe.seasonNumber:02}")
                except TypeError:
                    logger.error(f"Show [{pm}]: Invalid episode: {pe}")
                continue

            yield pm, tm, pe, te


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
        logger.info("Server version {} updated at: {}".format(server.version, server.updatedAt))
        logger.info("Recently added: {}".format(server.library.recentlyAdded()[:5]))

    if movies:
        for pm, tm in for_each_pair(plex.movie_sections, trakt):
            sync_collection(pm, tm, trakt, trakt_movie_collection)
            sync_ratings(pm, tm, plex, trakt)
            sync_watched(pm, tm, plex, trakt, trakt_watched_movies)

    if tv:
        for pm, tm, pe, te in for_each_episode(plex.show_sections, trakt):
            sync_show_collection(pm, tm, pe, te, trakt)
            sync_show_watched(pm, tm, pe, te, trakt_watched_shows, plex, trakt)

            # add to plex lists
            listutil.addPlexItemToLists(te.instance.trakt, pe)

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

    logger.info(f"Syncing with Plex {CONFIG['PLEX_USERNAME']} and Trakt {CONFIG['TRAKT_USERNAME']}")
    logger.info(f"Syncing TV={tv}, Movies={movies}")

    with measure_time("Completed full sync"):
        sync_all(movies=movies, tv=tv)
