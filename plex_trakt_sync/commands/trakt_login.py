from json import JSONDecodeError

import click
import trakt.core
from trakt.errors import ForbiddenException

from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.style import title, success, error
from plex_trakt_sync.trakt_api import TraktApi

TRAKT_LOGIN_SUCCESS = success(
    "You are now logged into Trakt. "
    "Your Trakt credentials have been added in .env and .pytrakt.json files."
)


def trakt_authenticate():
    click.echo(title("Sign in to Trakt"))
    trakt.core.AUTH_METHOD = trakt.core.DEVICE_AUTH

    while True:
        client_id, client_secret = trakt.core._get_client_info()
        try:
            return trakt.init(client_id=client_id, client_secret=client_secret, store=True)
        except (ForbiddenException, JSONDecodeError) as e:
            click.echo(error(f"Log in to Trakt failed: {e}, Try again."))


@click.command()
def trakt_login():
    """
    Log in to Trakt Account to obtain Access Token.
    """

    trakt_authenticate()
    api = TraktApi()
    user = api.me.username

    CONFIG["TRAKT_USERNAME"] = user
    CONFIG.save()

    click.echo(TRAKT_LOGIN_SUCCESS)
