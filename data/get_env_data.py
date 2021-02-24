from plexapi.myplex import MyPlexAccount
import utils
from os import path
import trakt
import trakt.core
import trakt.users
import stdiomask

trakt.core.CONFIG_PATH = path.join(path.dirname(path.abspath(__file__)), ".pytrakt.json")
env_file = path.join(path.dirname(path.abspath(__file__)), ".env")
print("")
plex_needed = utils.input_yesno("Are you logged into hawke.one with your Plex account? (almost certainly yes)")
if plex_needed:
    username = input("    Please enter your Plex username: ")
    # password = input("    Please enter your Plex password: ")
    password = stdiomask.getpass(prompt='    Please enter your Plex password: ')
    print("\nYour server name is displayed when viewing a Plex library at https://app.plex.tv/desktop \n    (top left under the library title) and will likely be:")
    print("    Gold Class = plex1.hawke.one")
    print("    Night Wathcmen = plex2.hawke.one or plex4.hawke.one")
    print("    Kings Guard = plex3.hawke.one")
    servername = input("\n    Please enter the hawke.one server name: ")
    account = MyPlexAccount(username, password)
    plex = account.resource(servername).connect()  # returns a PlexServer instance
    token = plex._token
    users = account.users()
    if users:
        print("\n    The folowing managed Plex user(s) were found:")
        for user in users:
            if user.friend is True:
                print("        " + user.title)
        print("\nIf you want to use a managed user enter its username, or")
        name = input("if you want to use your main account (most likely) just press enter: ")
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
else:
    with open(env_file, "w") as txt:
        txt.write("PLEX_USERNAME=-\n")
        txt.write("PLEX_TOKEN=-\n")
        txt.write("PLEX_BASEURL=http://localhost:32400\n")

trakt.core.AUTH_METHOD=trakt.core.DEVICE_AUTH
print(" ")
print("Create the required Trakt client ID and secret by completing the following steps:")
print("    1 - Login to Trakt here: http://trakt.tv/oauth/applications")
print("    2 - Press the NEW APPLICATION button")
print("    3 - Name = hawke.one")
print("    4 - Redirect url = urn:ietf:wg:oauth:2.0:oob")
print("    5 - Press the SAVE APP button")
print("    6 - Copy and paste the displayed Client ID and Secret as requested below\n")
client_id, client_secret = trakt.core._get_client_info()
trakt.init(client_id=client_id, client_secret=client_secret, store=True)
trakt_user = trakt.users.User('me')
with open(env_file, "a") as txt:
    txt.write("TRAKT_USERNAME=" + trakt_user.username + "\n")
print(" ")
print("All done! \nYou can now enjoy sync! \n\nYou can adjust settings by editing the config.json file,")
print("or change Plex / Trakt accounts by deleting the .env and .pytrakt.json files.")
print(" ")
print("PLEASE NOTE")
print("Your initial sync will take some time.") 
print("Information is then cached to speed up future syncs, however please bear in mind that hawke.one has a VERY large library.")
print(" ")