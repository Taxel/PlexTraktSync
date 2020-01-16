from plexapi.myplex import MyPlexAccount
import utils
from os import path
import trakt
import trakt.core

trakt.core.CONFIG_PATH = path.join(path.dirname(path.abspath(__file__)), ".pytrakt.json")
env_file = path.join(path.dirname(path.abspath(__file__)), ".env")

plex_needed = utils.input_yesno("Are you logged into this server with a Plex account?")
if plex_needed:
    username = input("Please enter your Plex username: ")
    password = input("Please enter your Plex password: ")
    servername = input("Now enter the server name: ")
    account = MyPlexAccount(username, password)
    plex = account.resource(servername).connect()  # returns a PlexServer instance
    with open(env_file, 'w') as txt:
        txt.write("PLEX_TOKEN=" + plex._token + "\n")
    print("Your Plex token has been added in .env file: PLEX_TOKEN=" + plex._token)
else:
    with open(env_file, "w") as txt:
        txt.write("PLEX_TOKEN=-\n")

trakt.APPLICATION_ID = '65370'
trakt.core.AUTH_METHOD=trakt.core.OAUTH_AUTH
trakt_user = input("Please input your Trakt username: ")
trakt.init(trakt_user, store=True)
with open(env_file, "a") as txt:
    txt.write("TRAKT_USERNAME=" + trakt_user + "\n")
print("You are now logged into Trakt. Your Trakt credentials have been added in .env and .pytrakt.json files.")
print("You can enjoy sync! \nCheck config.json to adjust settings.")
print("If you want to change Plex or Trakt account, just edit or remove .env and .pytrakt.json files.")