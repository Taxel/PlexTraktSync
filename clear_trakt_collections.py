# deletes everything in trakt's collection
# dangerous!
from dotenv import load_dotenv
from os import getenv
import trakt.users
import sys

def main():
    load_dotenv()
    trakt_user = trakt.users.User(getenv('TRAKT_USERNAME'))
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
