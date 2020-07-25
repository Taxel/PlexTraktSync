from plexapi.myplex import MyPlexAccount
from dotenv import load_dotenv
import utils
from os import getenv, path
import trakt
import trakt.core

trakt.core.CONFIG_PATH = path.join(path.dirname(path.abspath(__file__)), ".pytrakt.json")
env_file = path.join(path.dirname(path.abspath(__file__)), ".env")

load_dotenv()
PLEX_BASEURL = getenv("PLEX_BASEURL")
PLEX_USERNAME = getenv("PLEX_USERNAME")
PLEX_TOKEN = getenv("PLEX_TOKEN")
TRAKT_USERNAME = getenv("TRAKT_USERNAME")

CONFIG = utils.load_json(trakt.core.CONFIG_PATH)
CLIENT_ID = CONFIG.get("CLIENT_ID")
CLIENT_SECRET = CONFIG.get("CLIENT_SECRET")

plex_needed = utils.input_yesno("Are you logged into this server with a Plex account?")
if plex_needed:
    PLEX_USERNAME = utils.input_text("Please enter your Plex username", PLEX_USERNAME)
    password = utils.input_hidden("Please enter your Plex password: ")
    servername = input("Now enter the server name: ")
    account = MyPlexAccount(PLEX_USERNAME, password)
    plex = account.resource(servername).connect()  # returns a PlexServer instance
    token = plex._token
    users = account.users()
    if users:
        print("Managed user(s) found:")
        for user in users:
            if user.friend == True:
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
    PLEX_BASEURL = plex._baseurl
    PLEX_USERNAME = username
    PLEX_TOKEN = token

trakt.core.AUTH_METHOD=trakt.core.DEVICE_AUTH
TRAKT_USERNAME = utils.input_text("Please input your Trakt username", TRAKT_USERNAME)
client_id, client_secret = trakt.core._get_client_info()
trakt.init(client_id=client_id, client_secret=client_secret, store=True)

with open(env_file, "w") as txt:
    txt.write("TRAKT_USERNAME={0}\n".format(TRAKT_USERNAME))
    txt.write("PLEX_USERNAME={0}\n".format(PLEX_USERNAME))
    txt.write("PLEX_TOKEN={0}\n".format(PLEX_TOKEN))
    txt.write("PLEX_BASEURL={0}\n".format(PLEX_BASEURL))

print("You are now logged into Trakt. Your Trakt credentials have been added in .env and .pytrakt.json files.")
print("You can enjoy sync!")
print("")
print("Check config.json to adjust settings.")
print("If you want to change Plex or Trakt account, just edit or remove .env and .pytrakt.json files.")
