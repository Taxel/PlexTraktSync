from plexapi.myplex import MyPlexAccount
import utils
import trakt
import trakt.core


plex_needed = utils.input_yesno("Are you logged into this server with a Plex account?")
if plex_needed:
    username = input("Please enter your Plex username: ")
    password = input("Please enter your Plex password: ")
    servername = input("Now enter the server name: ")
    account = MyPlexAccount(username, password)
    plex = account.resource(servername).connect()  # returns a PlexServer instance
    print("Copy this Plex token to the .env file:", plex._token)
else:
    print("Add this as the PLEX_TOKEN in the .env file: PLEX_TOKEN=-")

trakt.APPLICATION_ID = '65370'
trakt.core.AUTH_METHOD=trakt.core.OAUTH_AUTH
trakt_user = input("Please input your Trakt username: ")
trakt.init(trakt_user, store=True)
print("You are now logged into Trakt. Add your username in .env: TRAKT_USER=" + trakt_user)
print("Once the PLEX_TOKEN and TRAKT_USER are in your .env file, you can run 'python3 plex.py' and enjoy!")