import trakt
from plex_trakt_sync.path import pytrakt_file
from plex_trakt_sync.plex_api import PlexLibrarySection, PlexApi
from plex_trakt_sync.trakt_api import TraktApi

trakt.core.CONFIG_PATH = pytrakt_file
import trakt.errors
import trakt.movies
import trakt.tv
import trakt.sync
import trakt.users
import trakt.core
from time import time, sleep
import datetime
from json.decoder import JSONDecodeError

from plex_trakt_sync import pytrakt_extensions
from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.logging import logging
from plex_trakt_sync.requests_cache import requests_cache

trakt_post_wait = 1.2  # delay in sec between trakt post requests to respect rate limit


def sync_ratings(pm, tm, plex: PlexApi, trakt: TraktApi):
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


def process_movie_section(section: PlexLibrarySection, watched_set, listutil, collection, trakt_api: TraktApi, plex_api: PlexApi):
    # args: a section of plex movies, a set comprised of the trakt ids of all watched movies and a dict with key=slug and value=rating (1-10)

    ###############
    # Sync movies with trakt
    ###############

    logging.info("Now working on movie section {} containing {} elements".format(section.title, len(section)))
    for it in section.items():
        movie = it.item
        if not it.provider:
            logging.error('Movie [{} ({})]: Unrecognized GUID {}'.format(movie.title, movie.year, movie.guid))
            continue

        # search and sync movie
        m = trakt_api.find_movie(it)
        if m is None:
            logging.warning(f"Movie [{movie.title} ({movie.year})]: Not found. Skipping")
            continue

        guid = it.guid
        try:
            last_time = time()
            if CONFIG['sync']['collection']:
                # add to collection if necessary
                if m.trakt not in collection:
                    retry = 0
                    while retry < 5:
                        try:
                            last_time = respect_trakt_rate(last_time)
                            m.add_to_library()
                            logging.info('Movie [{} ({})]: Added to trakt collection'.format(
                                movie.title, movie.year))
                            break
                        except trakt.errors.RateLimitException as e:
                            delay = int(e.response.headers.get("Retry-After", 1))
                            logging.warning(
                                "Movie [{} ({})]: Rate Limited on adding to collection. Sleeping {} sec from trakt (GUID: {})".format(movie.title, movie.year, delay, guid))
                            sleep(delay)
                            retry += retry
                    if retry == 5:
                        logging.warning(
                            "Movie [{} ({})]: Rate Limited 5 times on watched update. Abort trakt request.".format(movie.title, movie.year))
            # compare ratings
            if CONFIG['sync']['ratings']:
                sync_ratings(it, m, plex_api, trakt_api)

            # sync watch status
            if CONFIG['sync']['watched_status']:
                watchedOnPlex = movie.isWatched
                watchedOnTrakt = m.trakt in watched_set
                if watchedOnPlex is not watchedOnTrakt:
                    # if watch status is not synced
                    # send watched status from plex to trakt
                    if watchedOnPlex:
                        retry = 0
                        while retry < 5:
                            try:
                                last_time = respect_trakt_rate(last_time)
                                with requests_cache.disabled():
                                    seen_date = (movie.lastViewedAt if movie.lastViewedAt else datetime.now())
                                    m.mark_as_seen(seen_date.astimezone(datetime.timezone.utc))
                                logging.info("Movie [{} ({})]: marking as watched on Trakt...".format(
                                    movie.title, movie.year))
                                break
                            except ValueError:  # for py<3.6
                                with requests_cache.disabled():
                                    m.mark_as_seen(seen_date)
                            except trakt.errors.RateLimitException as e:
                                delay = int(e.response.headers.get("Retry-After", 1))
                                logging.warning(
                                    "Movie [{} ({})]: Rate Limited on watched update. Sleeping {} sec from trakt (GUID: {})".format(movie.title, movie.year, delay, guid))
                                sleep(delay)
                                retry += retry
                        if retry == 5:
                            logging.warning(
                                "Movie [{} ({})]: Rate Limited 5 times on watched update. Abort trakt request.".format(movie.title, movie.year))
                    # set watched status if movie is watched on trakt
                    elif watchedOnTrakt:
                        logging.info("Movie [{} ({})]: marking as watched in Plex...".format(
                            movie.title, movie.year))
                        with requests_cache.disabled():
                            movie.markWatched()
            # add to plex lists
            listutil.addPlexItemToLists(m.trakt, movie)

            logging.debug("Movie [{} ({})]: Finished sync".format(
                movie.title, movie.year))
        except trakt.errors.NotFoundException:
            logging.error(
                "Movie [{} ({})]: GUID {} not found on trakt".format(movie.title, movie.year, it.guid))
        except trakt.errors.RateLimitException as e:
            delay = int(e.response.headers.get("Retry-After", 1))
            logging.warning(
                "Movie [{} ({})]: Rate Limited. Sleeping {} sec from trakt (GUID: {})".format(movie.title, movie.year, delay, guid))
            sleep(delay)
        except Exception as e:
            logging.error(
                "Movie [{} ({})]: {} (GUID: {})".format(movie.title, movie.year, e, it.guid))


def process_show_section(s, watched_set, listutil):
    with requests_cache.disabled():
        allShows = s.all()
    logging.info("Now working on show section {} containing {} elements".format(s.title, len(allShows)))
    for show in allShows:
        guid = show.guid
        if guid.startswith('local') or 'agents.none' in guid:
            # ignore this guid, it's not matched
            logging.warning("Show [{} ({})]: GUID is local, ignoring".format(
                show.title, show.year))
            continue
        elif 'thetvdb' in guid:
            x = guid.split('//')[1]
            x = x.split('?')[0]
            provider = 'tvdb'
        elif 'themoviedb' in guid:
            x = guid.split('//')[1]
            x = x.split('?')[0]
            provider = 'tmdb'
        elif 'xbmcnfotv' in guid:
            x = guid.split('//')[1]
            x = x.split('?')[0]
            provider = CONFIG['xbmc-providers']['shows']
        else:
            logging.error("Show [{} ({})]: Unrecognized GUID {}".format(
                show.title, show.year, guid))
            continue

        try:
            # find show
            logging.debug("Show [{} ({})]: Started sync".format(
                show.title, show.year))
            search = trakt.sync.search_by_id(x, id_type=provider)
            trakt_show = None
            # look for the first tv show in the results
            for result in search:
                if type(result) is trakt.tv.TVShow:
                    trakt_show = result
                    break
            if trakt_show is None:
                logging.error("Show [{} ({})]: Did not find on Trakt. Aborting. GUID: {}".format(show.title, show.year, guid))
                continue
            with requests_cache.disabled():
                trakt_collected = pytrakt_extensions.collected(trakt_show.trakt)
            start_time = last_time = time()
            # this lookup-table is accessible via lookup[season][episode]
            with requests_cache.disabled():
                lookup = pytrakt_extensions.lookup_table(trakt_show)

            logging.debug("Show [{} ({})]: Generated LUT in {} seconds".format(
                show.title, show.year, (time() - start_time)))

            # loop over episodes in plex db
            for episode in show.episodes():
                try:
                    eps = lookup[episode.seasonNumber][episode.index]
                except KeyError:
                    try:
                        logging.warning("Show [{} ({})]: Key not found, did not record episode S{:02}E{:02}".format(
                            show.title, show.year, episode.seasonNumber, episode.index))
                    except TypeError:
                        logging.error("Show [{} ({})]: Invalid episode {}".format(show.title, show.year, episode))
                    continue
                watched = watched_set.get_completed(
                    trakt_show.trakt, episode.seasonNumber, episode.index)
                collected = trakt_collected.get_completed(
                    episode.seasonNumber, episode.index)
                # sync collected
                if CONFIG['sync']['collection']:
                    if not collected:
                        retry = 0
                        while retry < 5:
                            try:
                                last_time = respect_trakt_rate(last_time)
                                with requests_cache.disabled():
                                    eps.instance.add_to_library()
                                logging.info("Show [{} ({})]: Collected episode S{:02}E{:02}".format(
                                    show.title, show.year, episode.seasonNumber, episode.index))
                                break
                            except JSONDecodeError as e:
                                logging.error(
                                    "JSON decode error: {}".format(str(e)))
                            except trakt.errors.RateLimitException as e:
                                delay = int(e.response.headers.get("Retry-After", 1))
                                logging.warning("Show [{} ({})]: Rate limit on collected episode S{:02}E{:02}. Sleeping {} sec from trakt".format(
                                    show.title, show.year, episode.seasonNumber, episode.index, delay))
                                sleep(delay)
                                retry += retry
                        if retry == 5:
                            logging.warning(
                                "Show [{} ({})]: Rate Limited 5 times on collected episode S{:02}E{:02}. Abort trakt request.".format(show.title, show.year, episode.seasonNumber, episode.index))
                # sync watched status
                if CONFIG['sync']['watched_status']:
                    if episode.isWatched != watched:
                        if episode.isWatched:
                            retry = 0
                            while retry < 5:
                                try:
                                    last_time = respect_trakt_rate(last_time)
                                    with requests_cache.disabled():
                                        seen_date = (episode.lastViewedAt if episode.lastViewedAt else datetime.now())
                                        eps.instance.mark_as_seen(seen_date.astimezone(datetime.timezone.utc))
                                    logging.info("Show [{} ({})]: Marked as watched on trakt: episode S{:02}E{:02}".format(
                                        show.title, show.year, episode.seasonNumber, episode.index))
                                    break
                                except JSONDecodeError as e:
                                    logging.error(
                                        "JSON decode error: {}".format(str(e)))
                                except ValueError:  # for py<3.6
                                    with requests_cache.disabled():
                                        eps.instance.mark_as_seen(seen_date)
                                except trakt.errors.RateLimitException as e:
                                    delay = int(e.response.headers.get("Retry-After", 1))
                                    logging.warning("Show [{} ({})]: Rate limit on watched episode S{:02}E{:02}. Sleep {} sec from trakt".format(
                                        show.title, show.year, episode.seasonNumber, episode.index, delay))
                                    retry += retry
                                    sleep(delay)
                            if retry == 5:
                                logging.warning(
                                    "Show [{} ({})]: Rate Limited 5 times on collected episode S{:02}E{:02}. Abort trakt request.".format(show.title, show.year, episode.seasonNumber, episode.index))
                        elif watched:
                            with requests_cache.disabled():
                                episode.markWatched()
                            logging.info("Show [{} ({})]: Marked as watched on plex: episode S{:02}E{:02}".format(
                                show.title, show.year, episode.seasonNumber, episode.index))
                        else:
                            logging.warning("Episode.isWatched: {}, watched: {} isWatched != watched: {}".format(
                                episode.isWatched, watched, episode.isWatched != watched))
                    logging.debug("Show [{} ({})]: Synced episode S{:02}E{:02}".format(
                        show.title, show.year, episode.seasonNumber, episode.index))
                # add to plex lists
                listutil.addPlexItemToLists(eps.instance.trakt, episode)
            logging.debug("Show [{} ({})]: Finished sync".format(
                show.title, show.year))
        except trakt.errors.NotFoundException:
            logging.error("Show [{} ({})]: GUID {} not found on trakt".format(
                show.title, show.year, guid))
        except trakt.errors.RateLimitException as e:
            delay = int(e.response.headers.get("Retry-After", 1))
            logging.debug(
                "Show [{} ({})]: Rate Limited. Sleeping {} sec from trakt".format(show.title, show.year, delay))
            sleep(delay)
        except Exception as e:
            logging.error("Show [{} ({})]: {} (GUID {})".format(
                show.title, show.year, e, guid))


def respect_trakt_rate(last_time):
    diff_time = time() - last_time
    if diff_time < trakt_post_wait:
        sleep(trakt_post_wait - diff_time)
    return time()
