from __future__ import annotations

from json import JSONDecodeError
from os.path import exists
from typing import TYPE_CHECKING

from rich.prompt import Prompt
from trakt.errors import ForbiddenException

from plextraktsync.factory import factory
from plextraktsync.path import pytrakt_file
from plextraktsync.style import error, prompt, success, title

if TYPE_CHECKING:
    from plextraktsync.trakt.TraktApi import TraktApi

PROMPT_TRAKT_CLIENT_ID = prompt("Please enter your client id")
PROMPT_TRAKT_CLIENT_SECRET = prompt("Please enter your client secret")
TRAKT_LOGIN_SUCCESS = success("You are now logged into Trakt. Your Trakt credentials have been added in .env and .pytrakt.json files.")


def trakt_authenticate(api: TraktApi):
    print = factory.print

    print(title("Sign in to Trakt"))

    print("If you do not have a Trakt client ID and secret:")
    print("      1 - Open https://trakt.tv/oauth/applications on any computer")
    print("      2 - Login to your Trakt account")
    print("      3 - Press the NEW APPLICATION button")
    print("      4 - Set the NAME field = plex")
    print("      5 - Set the REDIRECT URL field = urn:ietf:wg:oauth:2.0:oob")
    print("      6 - Press the SAVE APP button")
    print("")

    while True:
        client_id = Prompt.ask(PROMPT_TRAKT_CLIENT_ID)
        client_secret = Prompt.ask(PROMPT_TRAKT_CLIENT_SECRET, password=True)

        print("Attempting to authenticate with Trakt")
        try:
            return api.device_auth(client_id=client_id, client_secret=client_secret)
        except (ForbiddenException, JSONDecodeError) as e:
            print(error(f"Log in to Trakt failed: {e}, Try again."))


def has_trakt_token():
    if not exists(pytrakt_file):
        return False

    CONFIG = factory.config
    return CONFIG["TRAKT_USERNAME"] is not None


def trakt_login_autoconfig():
    login()


def trakt_login():
    """
    Log in to Trakt Account to obtain Access Token.
    """
    login()


def login():
    print = factory.print
    api = factory.trakt_api
    trakt_authenticate(api)
    user = api.me.username

    CONFIG = factory.config
    CONFIG["TRAKT_USERNAME"] = user
    CONFIG.save()

    print(TRAKT_LOGIN_SUCCESS)
