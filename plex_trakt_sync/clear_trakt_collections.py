import trakt
from plex_trakt_sync.path import pytrakt_file
trakt.core.CONFIG_PATH = pytrakt_file
import trakt.users

def clear_trakt_collections():
    trakt_user = trakt.users.User('me')
    coll = trakt_user.movie_collection
    for movie in coll:
        print("Deleting", movie.title)
        movie.remove_from_library()
    coll = trakt_user.show_collection
    for show in coll:
        print("Deleting", show.title)
        show.remove_from_library()
