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
PROMPT_TRAKT_CLIENT_SECRET = prompt("Please enter your client secret (leave blank if your app has none)")
TRAKT_LOGIN_SUCCESS = success("You are now logged into Trakt. Your Trakt credentials have been added in .env and .pytrakt.json files.")

TRAKT_URL = "https://trakt.tv"
TRAKT_APP_URL = "https://developer.trakt.tv/apps/new"
TRAKT_REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


def print_create_app_instructions(print):
    print("If you do not have a Trakt app yet:")
    print(f"      1 - Open {TRAKT_APP_URL} on any computer")
    print("      2 - Set the App name field = plex")
    print("      3 - Leave the Description field blank (optional)")
    print(f"      4 - Set the Redirect URIs field = {TRAKT_REDIRECT_URI}")
    print("      5 - Leave the Allowed origins field blank (optional)")
    print("      6 - Press the Create app button")
    print("      7 - Copy the generated Client ID")
    print("")
    print("Note: a Client Secret is only shown for older apps and is optional.")


def trakt_authenticate(api: TraktApi):
    print = factory.print

    print(title(f"Sign in to Trakt - {TRAKT_URL}"))
    print_create_app_instructions(print)

    while True:
        client_id = Prompt.ask(PROMPT_TRAKT_CLIENT_ID)
        client_secret = Prompt.ask(PROMPT_TRAKT_CLIENT_SECRET, password=True, default="", show_default=False)

        print("Attempting to authenticate with Trakt")
        try:
            return api.device_auth(client_id=client_id, client_secret=client_secret or None)
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
