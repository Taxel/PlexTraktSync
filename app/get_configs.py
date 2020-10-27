import json
import sys
from os import path
from sys import argv

import trakt
import trakt.users
from plexapi.myplex import MyPlexAccount


def main():
    if len(sys.argv) == 1:
        get_plex_credentials()
        get_trakt_credentials()
    elif sys.argv[1] == 'plex':
        get_plex_credentials()
    elif sys.argv[1] == 'trakt':
        get_trakt_credentials()

    print("\nConfig files generation completed. You can now run the docker container.")
    print("Don't forget to mount the data folder as a docker volume under /app/data. Check README for detailed instructions.")
    print("Check config.json to adjust app settings.")


def get_plex_credentials():
    plex_config = {}
    plex_config_file = path.join(path.dirname(path.abspath(__file__)), "data/plex_config.json")

    print("-- Plex --")
    username = input("Plex username: ")
    password = input("Plex password: ")
    servername = input("Server name: ")
    base_url = input("Server base url: ")
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
                print("Impossible to find the managed user \'"+name+"\' on this server!")
                name = "_wrong"

    plex_config['PLEX_USERNAME'] = username
    plex_config['PLEX_TOKEN'] = token
    plex_config['BASE_URL'] = base_url

    with open(plex_config_file, 'w') as fp:
        json.dump(plex_config, fp)

    print(f"Plex credentials for {username} have been added in data/plex_config.json")


def get_trakt_credentials():
    print("-- Trakt --")
    trakt.core.CONFIG_PATH = path.join(path.dirname(path.abspath(__file__)), "data/trakt_config.json")
    trakt.core.AUTH_METHOD = trakt.core.DEVICE_AUTH
    client_id, client_secret = trakt.core._get_client_info()
    trakt.init(client_id=client_id, client_secret=client_secret, store=True)

    print(f"Trakt credentials for {trakt.users.User('me')} have been added in data/trakt_config.json")


if __name__ == "__main__":
    main()
