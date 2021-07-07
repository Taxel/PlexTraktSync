from json import JSONDecodeError
from os.path import exists

import click
from trakt.errors import ForbiddenException

from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.factory import factory
from plex_trakt_sync.path import pytrakt_file
from plex_trakt_sync.style import title, success, error, prompt
from plex_trakt_sync.trakt_api import TraktApi

PROMPT_TRAKT_CLIENT_ID = prompt("Please enter your client id")
PROMPT_TRAKT_CLIENT_SECRET = prompt("Please enter your client secret")
TRAKT_LOGIN_SUCCESS = success(
    "You are now logged into Trakt. "
    "Your Trakt credentials have been added in .env and .pytrakt.json files."
)


def trakt_authenticate(api: TraktApi):
    click.echo(title("Sign in to Trakt"))

    click.echo("If you do not have a client ID and secret. Please visit the following url to create them.")
    click.echo("  https://trakt.tv/oauth/applications")
    click.echo("")

    while True:
        client_id = click.prompt(PROMPT_TRAKT_CLIENT_ID, type=str)
        client_secret = click.prompt(PROMPT_TRAKT_CLIENT_SECRET, type=str)

        click.echo("Attempting to authenticate with Trakt")
        try:
            return api.device_auth(client_id=client_id, client_secret=client_secret)
        except (ForbiddenException, JSONDecodeError) as e:
            click.echo(error(f"Log in to Trakt failed: {e}, Try again."))


def has_trakt_token():
    if not exists(pytrakt_file):
        return False
    return CONFIG["TRAKT_USERNAME"] is not None


@click.command()
def trakt_login():
    """
    Log in to Trakt Account to obtain Access Token.
    """

    api = factory.trakt_api()
    trakt_authenticate(api)
    user = api.me.username

    CONFIG["TRAKT_USERNAME"] = user
    CONFIG.save()

    click.echo(TRAKT_LOGIN_SUCCESS)
