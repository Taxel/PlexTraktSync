import plexapi.server
import requests_cache
import trakt
from plex_trakt_sync.path import pytrakt_file, env_file, trakt_cache
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
from plex_trakt_sync.trakt_list_util import TraktListUtil
from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.logging import logging

requests_cache.install_cache(trakt_cache)
trakt_post_wait = 1.2  # delay in sec between trakt post requests to respect rate limit


def process_movie_section(s, watched_set, ratings_dict, listutil, collection):
    # args: a section of plex movies, a set comprised of the trakt ids of all watched movies and a dict with key=slug and value=rating (1-10)

    ###############
    # Sync movies with trakt
    ###############
    with requests_cache.disabled():
        allMovies = s.all()
    logging.info("Now working on movie section {} containing {} elements".format(s.title, len(allMovies)))
    for movie in allMovies:
        # find id to search movie
        guid = movie.guid
        if guid.startswith('plex://movie/'):
            if len(movie.guids) > 0:
                logging.debug("trying first alternative guid: " + str(movie.guids[0].id))
                guid = movie.guids[0].id
        x = provider = None
        if guid.startswith('local') or 'agents.none' in guid:
            # ignore this guid, it's not matched
            logging.warning("Movie [{} ({})]: GUID ({}) is local or none, ignoring".format(
                movie.title, movie.year, guid))
            continue
        elif 'imdb' in guid:
            x = guid.split('//')[1]
            x = x.split('?')[0]
            provider = 'imdb'
        elif 'themoviedb' in guid or 'tmdb' in guid:
            x = guid.split('//')[1]
            x = x.split('?')[0]
            provider = 'tmdb'
        elif 'xbmcnfo' in guid:
            x = guid.split('//')[1]
            x = x.split('?')[0]
            provider = CONFIG['xbmc-providers']['movies']
        else:
            logging.error('Movie [{} ({})]: Unrecognized GUID {}'.format(
                movie.title, movie.year, movie.guid))
            continue
        # search and sync movie
        try:
            search = trakt.sync.search_by_id(x, id_type=provider)
            m = None
            # look for the first movie in the results
            for result in search:
                if type(result) is trakt.movies.Movie:
                    m = result
                    break
            if m is None:
                logging.error('Movie [{} ({})]: Not found. Aborting'.format(
                    movie.title, movie.year))
                continue
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
                if m.slug in ratings_dict:
                    trakt_rating = int(ratings_dict[m.slug])
                else:
                    trakt_rating = None
                plex_rating = int(
                    movie.userRating) if movie.userRating is not None else None
                identical = plex_rating is trakt_rating
                # plex rating takes precedence over trakt rating
                if plex_rating is not None and not identical:
                    retry = 0
                    while retry < 5:
                        try:
                            last_time = respect_trakt_rate(last_time)
                            with requests_cache.disabled():
                                m.rate(plex_rating)
                            logging.info("Movie [{} ({})]: Rating with {} on trakt".format(
                                movie.title, movie.year, plex_rating))
                            break
                        except trakt.errors.RateLimitException as e:
                            delay = int(e.response.headers.get("Retry-After", 1))
                            logging.warning(
                                "Movie [{} ({})]: Rate Limited on rating update. Sleeping {} sec from trakt (GUID: {})".format(movie.title, movie.year, delay, guid))
                            sleep(delay)
                            retry += retry
                    if retry == 5:
                        logging.warning(
                            "Movie [{} ({})]: Rate Limited 5 times on watched update. Abort trakt request.".format(movie.title, movie.year))
                elif trakt_rating is not None and not identical:
                    with requests_cache.disabled():
                        movie.rate(trakt_rating)
                    logging.info("Movie [{} ({})]: Rating with {} on plex".format(
                        movie.title, movie.year, trakt_rating))

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

            logging.info("Movie [{} ({})]: Finished sync".format(
                movie.title, movie.year))
        except trakt.errors.NotFoundException:
            logging.error(
                "Movie [{} ({})]: GUID {} not found on trakt".format(movie.title, movie.year, guid))
        except trakt.errors.RateLimitException as e:
            delay = int(e.response.headers.get("Retry-After", 1))
            logging.warning(
                "Movie [{} ({})]: Rate Limited. Sleeping {} sec from trakt (GUID: {})".format(movie.title, movie.year, delay, guid))
            sleep(delay)
        except Exception as e:
            logging.warning(
                "Movie [{} ({})]: {} (GUID: {})".format(movie.title, movie.year, e, guid))


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
            logging.info("Show [{} ({})]: Finished sync".format(
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


def get_plex_server():
    plex_token = CONFIG["PLEX_TOKEN"]
    plex_baseurl = CONFIG["PLEX_BASEURL"]
    plex_fallbackurl = CONFIG["PLEX_FALLBACKURL"]
    if plex_token == '-':
        plex_token = ""
    server = None
    # if connection fails, it will try :
    # 1. url expected by new ssl certificate
    # 2. url without ssl
    # 3. fallback url (localhost)
    try:
        server = plexapi.server.PlexServer(
            token=plex_token, baseurl=plex_baseurl)
    except plexapi.server.requests.exceptions.SSLError as e:
        m = "Plex connection error: {}, fallback url {} didn't respond either.".format(str(e), plex_fallbackurl)
        excep_msg = str(e.__context__)
        if "doesn't match '*." in excep_msg:
            hash_pos = excep_msg.find("*.") + 2
            new_hash = excep_msg[hash_pos:hash_pos + 32]
            end_pos = plex_baseurl.find(".plex.direct")
            new_plex_baseurl = plex_baseurl[:end_pos - 32] + new_hash + plex_baseurl[end_pos:]
            try:  # 1
                server = plexapi.server.PlexServer(
                    token=plex_token, baseurl=new_plex_baseurl)
                # save new url to .env
                with open(env_file, 'w') as txt:
                    txt.write("PLEX_USERNAME=" + CONFIG['PLEX_USERNAME'] + "\n")
                    txt.write("PLEX_TOKEN=" + plex_token + "\n")
                    txt.write("PLEX_BASEURL=" + new_plex_baseurl + "\n")
                    txt.write("PLEX_FALLBACKURL=" + plex_fallbackurl + "\n")
                    txt.write("TRAKT_USERNAME=" + CONFIG['TRAKT_USERNAME'] + "\n")
                logging.info("Plex server url changed to {}".format(new_plex_baseurl))
            except Exception:
                pass
        if server is None and plex_baseurl[:5] == "https":
            new_plex_baseurl = plex_baseurl.replace("https", "http")
            try:  # 2
                server = plexapi.server.PlexServer(
                    token=plex_token, baseurl=new_plex_baseurl)
                logging.warning("Switched to Plex unsecure connection because of SSLError.")
            except Exception:
                pass
    except Exception as e:
        m = "Plex connection error: {}, fallback url {} didn't respond either.".format(str(e), plex_fallbackurl)
        pass
    if server is None:
        try:  # 3
            server = plexapi.server.PlexServer(
                token=plex_token, baseurl=plex_fallbackurl)
            logging.warning("No response from {}, fallback to {}".format(plex_baseurl, plex_fallbackurl))
        except Exception:
            logging.error(m)
            print(m)
            exit(1)
    return server

def respect_trakt_rate(last_time):
    diff_time = time() - last_time
    if diff_time < trakt_post_wait:
        sleep(trakt_post_wait - diff_time)
    return time()

def main():

    start_time = time()
    listutil = TraktListUtil()
    logging.info("Starting sync Plex {} and Trakt {}".format(CONFIG['PLEX_USERNAME'], CONFIG['TRAKT_USERNAME']))
    # do not use the cache for account specific stuff as this is subject to change
    with requests_cache.disabled():
        try:
            trakt_user = trakt.users.User('me')
        except trakt.errors.OAuthException as e:
            m = "Trakt authentication error: {}".format(str(e))
            logging.error(m)
            exit(1)
        if CONFIG['sync']['liked_lists']:
            liked_lists = pytrakt_extensions.get_liked_lists()
        trakt_watched_movies = set(
            map(lambda m: m.trakt, trakt_user.watched_movies))
        logging.debug("Watched movies from trakt: {}".format(
            trakt_watched_movies))
        trakt_movie_collection = set(
            map(lambda m: m.trakt, trakt_user.movie_collection))
        # logging.debug("Movie collection from trakt:", trakt_movie_collection)
        trakt_watched_shows = pytrakt_extensions.allwatched()
        if CONFIG['sync']['watchlist']:
            listutil.addList(None, "Trakt Watchlist", traktid_list=list(
                map(lambda m: m.trakt, trakt_user.watchlist_movies)))
        # logging.debug("Movie watchlist from trakt:", trakt_movie_watchlist)
        user_ratings = trakt_user.get_ratings(media_type='movies')
    if CONFIG['sync']['liked_lists']:
        for lst in liked_lists:
            listutil.addList(lst['username'], lst['listname'])
    ratings = {}
    for r in user_ratings:
        ratings[r['movie']['ids']['slug']] = r['rating']
    logging.debug("Movie ratings from trakt: {}".format(ratings))
    logging.info('Loaded Trakt lists.')
    with requests_cache.disabled():
        plex = get_plex_server()
        logging.info("Server version {} updated at: {}".format(
            plex.version, plex.updatedAt))
        logging.info("Recently added: {}".format(
            plex.library.recentlyAdded()[:5]))
    with requests_cache.disabled():
        sections = plex.library.sections()
    for section in sections:
        if section.title in CONFIG['excluded-libraries']:
            continue
        # process movie sections
        section_start_time = time()
        if type(section) is plexapi.library.MovieSection:
            # clean_collections_in_section(section)
            logging.info("Processing section {}".format(section.title))
            process_movie_section(
                section, trakt_watched_movies, ratings, listutil, trakt_movie_collection)
        # process show sections
        elif type(section) is plexapi.library.ShowSection:
            logging.info("Processing section {}".format(section.title))
            process_show_section(section, trakt_watched_shows, listutil)
        else:
            continue

        timedelta = time() - section_start_time
        m, s = divmod(timedelta, 60)
        logging.warning("Completed section sync in " + (m>0) * "{:.0f} min ".format(m) + (s>0) * "{:.1f} seconds".format(s))

    listutil.updatePlexLists(plex)
    logging.info("Updated plex watchlist")
    timedelta = time() - start_time
    m, s = divmod(timedelta, 60)
    logging.info("Completed full sync in " + (m>0) * "{:.0f} min ".format(m) + (s>0) * "{:.1f} seconds".format(s))
