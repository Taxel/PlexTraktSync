from plexapi.myplex import MyPlexAccount
from plex_trakt_sync import util
import trakt.users

from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.path import pytrakt_file


def get_env_data():
    trakt.core.CONFIG_PATH = pytrakt_file
    plex_needed = util.input_yesno("-- Plex --\nAre you logged into this server with a Plex account?")
    if plex_needed:
        username = input("Please enter your Plex username: ")
        password = input("Please enter your Plex password: ")
        servername = input("Now enter the server name: ")
        account = MyPlexAccount(username, password)
        plex = account.resource(servername).connect()  # returns a PlexServer instance
        token = plex._token
        users = account.users()
        if users:
            print("Managed user(s) found:")
            for user in users:
                if user.friend is True:
                    print(user.title)
            print("If you want to use a managed user enter its username,")
            name = input("if you want to use your main account just press enter: ")
            while name:
                try:
                    useraccount = account.user(name)
                except:
                    if name != "_wrong":
                        print("Unknown username!")
                    name = input("Please enter a managed username (or just press enter to use your main account): ")
                    if not name:
                        print("Ok, continuing with your account " + username)
                        break
                    continue
                try:
                    token = account.user(name).get_token(plex.machineIdentifier)
                    username = name
                    break
                except:
                    print("Impossible to find the managed user \'" + name + "\' on this server!")
                    name = "_wrong"
        CONFIG["PLEX_USERNAME"] = username
        CONFIG["PLEX_TOKEN"] = token
        CONFIG["PLEX_BASEURL"] = plex._baseurl
        CONFIG["PLEX_FALLBACKURL"] = "http://localhost:32400"

        print("Plex token and baseurl for {} have been added in .env file:".format(username))
        print("PLEX_TOKEN={}".format(token))
        print("PLEX_BASEURL={}".format(plex._baseurl))
    else:
        CONFIG["PLEX_USERNAME"] = "-"
        CONFIG["PLEX_TOKEN"] = "-"
        CONFIG["PLEX_BASEURL"] = "http://localhost:32400"

    trakt.core.AUTH_METHOD = trakt.core.DEVICE_AUTH
    print("-- Trakt --")
    client_id, client_secret = trakt.core._get_client_info()
    trakt.init(client_id=client_id, client_secret=client_secret, store=True)
    trakt_user = trakt.users.User('me')
    CONFIG["TRAKT_USERNAME"] = trakt_user.username

    print("You are now logged into Trakt. Your Trakt credentials have been added in .env and .pytrakt.json files.")
    print("You can enjoy sync! \nCheck config.json to adjust settings.")
    print("If you want to change Plex or Trakt account, just edit or remove .env and .pytrakt.json files.")

    CONFIG.save()
