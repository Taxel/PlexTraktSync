import click
from plexapi.exceptions import NotFound

from plex_trakt_sync.requests_cache import requests_cache
from plex_trakt_sync.plex_server import get_plex_server
from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.decorators import measure_time
from plex_trakt_sync.plex_api import PlexApi
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


def sync_show_collection(tm, pe, te, trakt: TraktApi):
    if not CONFIG['sync']['collection']:
        return

    collected = trakt.collected(tm)
    is_collected = collected.get_completed(pe.season_number, pe.episode_number)
    if is_collected:
        return

    logger.info(f"Add to Trakt Collection: {pe}")
    trakt.add_to_collection(te, pe)


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


def sync_show_watched(tm, pe, te, trakt_watched_shows, plex: PlexApi, trakt: TraktApi):
    if not CONFIG['sync']['watched_status']:
        return

    watched_on_plex = pe.item.isWatched
    watched_on_trakt = trakt_watched_shows.get_completed(tm.trakt, pe.season_number, pe.episode_number)

    if watched_on_plex == watched_on_trakt:
        return

    if watched_on_plex:
        logger.info(f"Marking as watched in Trakt: {pe}")
        trakt.mark_watched(te, pe.seen_date)
    elif watched_on_trakt:
        logger.info(f"Marking as watched in Plex: {pe}")
        plex.mark_watched(pe.item)


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

                    tm = trakt.find_by_media(pm)
                    if tm is None:
                        logger.warning(f"Skipping {pm}: Not found on Trakt")
                        continue

                    yield pm, tm


def for_each_episode(sections, trakt: TraktApi):
    for pm, tm in for_each_pair(sections, trakt):
        for tm, pe, te in for_each_show_episode(pm, tm, trakt):
            yield tm, pe, te


def find_show_episodes(show, plex: PlexApi, trakt: TraktApi):
    search = plex.search(show, libtype='show')
    for pm in search:
        tm = trakt.find_by_media(pm)
        for tm, pe, te in for_each_show_episode(pm, tm, trakt):
            yield tm, pe, te


def for_each_show_episode(pm, tm, trakt: TraktApi):
    for pe in pm.episodes():
        try:
            provider = pe.provider
        except NotFound as e:
            logger.error(f"Skipping {pe}: {e}")
            continue

        if provider in ["local", "none", "agents.none"]:
            logger.error(f"Skipping {pe}: Provider {provider} not supported")
            continue

        te = trakt.find_episode(tm, pe)
        if te is None:
            logger.warning(f"Skipping {pe}: Not found on Trakt")
            continue
        yield tm, pe, te


def sync_all(movies=True, tv=True, show=None):
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
        if show:
            it = find_show_episodes(show, plex, trakt)
        else:
            it = for_each_episode(plex.show_sections, trakt)

        for tm, pe, te in it:
            sync_show_collection(tm, pe, te, trakt)
            sync_show_watched(tm, pe, te, trakt_watched_shows, plex, trakt)

            # add to plex lists
            listutil.addPlexItemToLists(te.trakt, pe.item)

    with measure_time("Updated plex watchlist"):
        listutil.updatePlexLists(server)

    trakt.flush()


@click.command()
@click.option(
    "--show", "show",
    type=str,
    show_default=True, help="Sync specific show only"
)
@click.option(
    "--sync", "sync_option",
    type=click.Choice(["all", "movies", "tv"], case_sensitive=False),
    default="all",
    show_default=True, help="Specify what to sync"
)
def sync(sync_option: str, show: str):
    """
    Perform sync between Plex and Trakt
    """

    logger.info(f"Syncing with Plex {CONFIG['PLEX_USERNAME']} and Trakt {CONFIG['TRAKT_USERNAME']}")

    movies = sync_option in ["all", "movies"]
    tv = sync_option in ["all", "tv"]

    if show:
        movies = False
        tv = True
        logger.info(f"Syncing Show: {show}")
    elif not movies and not tv:
        click.echo("Nothing to sync!")
        return
    else:
        logger.info(f"Syncing TV={tv}, Movies={movies}")

    with measure_time("Completed full sync"):
        sync_all(movies=movies, tv=tv, show=show)
