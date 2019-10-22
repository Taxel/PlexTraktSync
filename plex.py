import plexapi
import trakt
import trakt.movies
import trakt.tv
import trakt.sync
import trakt.users
from plexapi.myplex import MyPlexAccount
from dotenv import load_dotenv
from os import getenv
import logging


def clean_collections_in_section(s):
    coll = s.collection()
    print(s.search(collection=[coll[0]]))


def process_movie_section(s, watched_set, ratings_dict):
    # args: a section of plex movies, a set comprised of the slugs of all watched movies and a dict with key=slug and value=rating (1-10)

    ###############
    # Sync movies with trakt
    ###############
    allMovies = s.all()
    for movie in allMovies:
        # find id to search movie
        guid = movie.guid
        x = provider = None
        if guid.startswith('local') or 'agents.none' in guid:
            # ignore this guid, it's not matched
            print("Movie guid is local, ignoring", movie.title)
            continue
        elif 'imdb' in guid:
            x = guid.split('//')[1]
            x = x.split('?')[0]
            provider = 'imdb'
        elif 'themoviedb' in guid:
            x = guid.split('//')[1]
            x = x.split('?')[0]
            provider = 'tmdb'
        else:
            print('Unrecognized guid:', movie.guid, movie.title)
            raise NotImplementedError()
        # search and sync movie
        try:
            search = trakt.sync.search_by_id(x, id_type=provider)
            # look for the first movie in the results
            for result in search:
                if type(result) is trakt.movies.Movie:
                    m = result
                    break
            m.add_to_library()
            if m.slug in ratings_dict:
                trakt_rating = ratings_dict[m.slug]
            else:
                trakt_rating = None
            plex_rating = movie.userRating
            # plex rating takes precedence over trakt rating
            if plex_rating is not None:
                m.rate(plex_rating)
                print("\tRating with {} on trakt".format(plex_rating))
            elif trakt_rating is not None:
                movie.rate(trakt_rating)
                print("\tRating with {} on plex".format(trakt_rating))
            watchedOnPlex = movie.isWatched
            watchedOnTrakt = m.slug in watched_set
            if watchedOnPlex is not watchedOnTrakt:
                # if watch status is not synced
                # send watched status from plex to trakt
                if watchedOnPlex:
                    print("\tmarking as watched on Trakt...")
                    m.mark_as_seen()
                # set watched status if movie is watched on trakt
                elif watchedOnTrakt:
                    print("\tmarking as watched in Plex...")
                    movie.markWatched()
            print("{} ({}) - ADDED TO LIBRARY".format(movie.title, movie.year))
        except trakt.errors.NotFoundException:
            print("{} ({}) - NOT FOUND".format(movie.title, movie.year))
            print(movie.guid)


def process_show_section(s):
    allShows = s.all()
    for show in allShows:
        guid = show.guid
        if guid.startswith('local'):
            # ignore this guid, it's not matched
            print("Show guid is local, ignoring", show.title)
            continue
        elif 'thetvdb' in guid:
            x = guid.split('//')[1]
            x = x.split('?')[0]
            provider = 'tvdb'
        else:
            print("Unrecognized guid:", guid, show.title)
            raise NotImplementedError()
        # elif 'themoviedb' in guid:
        #     x = guid.split('//')[1]
        #     x = x.split('?')[0]
        #     provider = 'tmdb'

        try:
            # find show
            print("Now working on show ", show.title)
            search = trakt.sync.search_by_id(x, id_type=provider)
            # look for the first tv show in the results
            for result in search:
                if type(result) is trakt.tv.TVShow:
                    trakt_show = result
                    break
            trakt_seasons = trakt_show.seasons
            # this lookup-table is accessible via lookup[season][episode]
            lookup = {}
            for season in trakt_seasons:
                episodes = season.episodes
                d = {}
                for episode in episodes:
                    d[episode.number] = episode
                lookup[season.season] = d

            # loop over episodes in plex db
            for episode in show.episodes():
                try:
                    eps = lookup[episode.seasonNumber][episode.index]
                    eps.add_to_library()
                    if episode.isWatched:
                        eps.mark_as_seen()
                except KeyError:
                    print("Key not found, did not record episode: {} s{:02}e{:02}".format(
                        trakt_show.title, episode.seasonNumber, episode.index))
            print("{} ({}) - ADDED TO LIBRARY".format(show.title, show.year))
        except trakt.errors.NotFoundException:
            print("{} ({}) - NOT FOUND".format(show.title, show.year))
            print(show.guid)


def main():
    load_dotenv()
    trakt_user = trakt.users.User(getenv('TRAKT_USERNAME'))
    watched_movies = set(map(lambda m: m.slug, trakt_user.watched_movies))
    user_ratings = trakt_user.get_ratings(media_type='movies')
    ratings = {}
    for r in user_ratings:
        ratings[r['movie']['ids']['slug']] = r['rating']
    #watched_shows = trakt_user.watched_shows
    plex = plexapi.server.PlexServer(token=getenv('PLEX_TOKEN'))
    sections = plex.library.sections()
    for section in sections:
        # process movie sections
        if type(section) is plexapi.library.MovieSection:
            #clean_collections_in_section(section)
            process_movie_section(section, watched_movies, ratings)
        # process show sections
        elif type(section) is plexapi.library.ShowSection:
            process_show_section(section)


if __name__ == "__main__":
    main()
