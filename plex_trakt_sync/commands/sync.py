import click

from plex_trakt_sync.media import MediaFactory, Media
from plex_trakt_sync.requests_cache import requests_cache
from plex_trakt_sync.plex_server import get_plex_server
from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.decorators import measure_time
from plex_trakt_sync.plex_api import PlexApi
from plex_trakt_sync.trakt_api import TraktApi
from plex_trakt_sync.trakt_list_util import TraktListUtil
from plex_trakt_sync.logging import logger
from plex_trakt_sync.version import git_version_info


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


def for_each_pair(sections, mf: MediaFactory):
    for section in sections:
        label = f"Processing {section.title}"
        with measure_time(label):
            pb = click.progressbar(section.items(), length=len(section), show_pos=True, label=label)
            with pb as items:
                for pm in items:
                    m = mf.resolve(pm)
                    if not m:
                        continue
                    yield m


def for_each_episode(sections, mf: MediaFactory):
    for m in for_each_pair(sections, mf):
        for me in for_each_show_episode(m, mf):
            yield me


def find_show_episodes(show, plex: PlexApi, mf: MediaFactory):
    search = plex.search(show, libtype='show')
    for pm in search:
        m = mf.resolve(pm)
        if not m:
            continue
        for me in for_each_show_episode(m, mf):
            yield me


def for_each_show_episode(m: Media, mf: MediaFactory):
    for pe in m.plex.episodes():
        me = mf.resolve(pe, m.trakt)
        if not me:
            continue

        me.show = m
        yield me


def sync_all(library=None, movies=True, tv=True, show=None, batch_size=None):
    with requests_cache.disabled():
        server = get_plex_server()
    listutil = TraktListUtil()
    plex = PlexApi(server)
    trakt = TraktApi(batch_size=batch_size)

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

    mf = MediaFactory(plex, trakt)
    if movies:
        for m in for_each_pair(plex.movie_sections(library=library), mf):
            sync_collection(m)
            sync_ratings(m)
            sync_watched(m)

            # add to plex lists
            listutil.addPlexItemToLists(m.trakt_id, m.plex.item)

    if tv:
        if show:
            it = find_show_episodes(show, plex, mf)
        else:
            it = for_each_episode(plex.show_sections(library=library), mf)

        for me in it:
            sync_collection(me)
            sync_watched(me)

            # add to plex lists
            listutil.addPlexItemToLists(me.trakt_id, me.plex.item)

    with measure_time("Updated plex watchlist"):
        listutil.updatePlexLists(server)

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
def sync(sync_option: str, library: str, show: str, batch_size: int):
    """
    Perform sync between Plex and Trakt
    """

    git_version = git_version_info()
    if git_version:
        logger.info(f"PlexTraktSync [{git_version}]")
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
        sync_all(movies=movies, library=library, tv=tv, show=show, batch_size=batch_size)
