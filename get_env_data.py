from plexapi.myplex import MyPlexAccount
import utils
from os import path
import trakt
import trakt.core
import trakt.users

trakt.core.CONFIG_PATH = path.join(path.dirname(path.abspath(__file__)), ".pytrakt.json")
env_file = path.join(path.dirname(path.abspath(__file__)), ".env")

plex_needed = utils.input_yesno("-- Plex --\nAre you logged into this server with a Plex account?")
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
                print("Impossible to find the managed user \'"+name+"\' on this server!")
                name = "_wrong"
    with open(env_file, 'w') as txt:
        txt.write("PLEX_USERNAME=" + username + "\n")
        txt.write("PLEX_TOKEN=" + token + "\n")
        txt.write("PLEX_BASEURL=" + plex._baseurl + "\n")
        txt.write("PLEX_FALLBACKURL=http://localhost:32400\n")
    print("Plex token and baseurl for {} have been added in .env file:".format(username))
    print("PLEX_TOKEN={}".format(token))
    print("PLEX_BASEURL={}".format(plex._baseurl))
else:
    with open(env_file, "w") as txt:
        txt.write("PLEX_USERNAME=-\n")
        txt.write("PLEX_TOKEN=-\n")
        txt.write("PLEX_BASEURL=http://localhost:32400\n")

trakt.core.AUTH_METHOD=trakt.core.DEVICE_AUTH
print("-- Trakt --")
client_id, client_secret = trakt.core._get_client_info()
trakt.init(client_id=client_id, client_secret=client_secret, store=True)
trakt_user = trakt.users.User('me')
with open(env_file, "a") as txt:
    txt.write("TRAKT_USERNAME=" + trakt_user.username + "\n")
print("You are now logged into Trakt. Your Trakt credentials have been added in .env and .pytrakt.json files.")
print("You can enjoy sync! \nCheck config.json to adjust settings.")
print("If you want to change Plex or Trakt account, just edit or remove .env and .pytrakt.json files.")