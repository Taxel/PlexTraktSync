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
from plex_trakt_sync.logging import logger as logging
from plex_trakt_sync.requests_cache import requests_cache

trakt_post_wait = 1.2  # delay in sec between trakt post requests to respect rate limit


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
