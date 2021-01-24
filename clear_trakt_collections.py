# deletes everything in trakt's collection
# dangerous!
import trakt
import sys
from os import path
trakt.core.CONFIG_PATH = path.join(path.dirname(path.abspath(__file__)), ".pytrakt.json")
import trakt.users


def main():
    trakt_user = trakt.users.User('me')
    coll = trakt_user.movie_collection
    for movie in coll:
        print("Deleting", movie.title)
        movie.remove_from_library()
    coll = trakt_user.show_collection
    for show in coll:
        print("Deleting", show.title)
        show.remove_from_library()


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != '-confirm':
        print("This script will delete every movie and show from your trakt collection. If you are sure you want to do that, rerun this script with the argument -confirm")
    else:
        main()
