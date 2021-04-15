from typing import List

import click
from click import Choice
from plexapi.exceptions import Unauthorized, NotFound
from plexapi.myplex import MyPlexAccount, MyPlexResource
from plexapi.server import PlexServer

from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.style import prompt, error, success, title, comment

PROMPT_PLEX_PASSWORD = prompt("Please enter your Plex password")
PROMPT_PLEX_USERNAME = prompt("Please enter your Plex username")
PROMPT_PLEX_RELOGIN = prompt("You already have Plex Access Token, do you want to log in again?")
PROMPT_MANAGED_USER = prompt("Do you want to use managed user instead of main account?")
SUCCESS_MESSAGE = success("Plex Media Server Authentication Token and base URL have been added to .env file")


def myplex_login(username, password):
    while True:
        username = click.prompt(PROMPT_PLEX_USERNAME, type=str, default=username)
        password = click.prompt(PROMPT_PLEX_PASSWORD, type=str, default=password, hide_input=True, show_default=False)
        try:
            return MyPlexAccount(username, password)
        except Unauthorized as e:
            click.echo(error(f"Log in to Plex failed: {e}, Try again."))


def choose_managed_user(account: MyPlexAccount):
    users = [u.title for u in account.users() if u.friend]
    if not users:
        return None

    click.echo(success("Managed user(s) found:"))
    users = sorted(users)
    for user in users:
        click.echo(f"- {user}")

    if not click.confirm(PROMPT_MANAGED_USER):
        return None

    # choice = prompt_choice(users)
    user = click.prompt(
        title("Please select:"),
        type=Choice(users),
        show_default=True,
    )

    # Sanity check, even the user can't input invalid user
    user_account = account.user(user)
    if user_account:
        return user

    return None


def prompt_server(servers: List[MyPlexResource]):
    def fmt_server(s):
        details = comment(f"{s.product}/{s.productVersion} on {s.device}: {s.platform}/{s.platformVersion}")
        return f"- {s.name}: [Last seen: {comment(str(s.lastSeenAt))}, Server: {details}]"

    owned_servers = [s for s in servers if s.owned]
    unowned_servers = [s for s in servers if not s.owned]

    server_names = []
    if owned_servers:
        click.echo(success(f"{len(owned_servers)} owned servers found:"))
        for s in owned_servers:
            click.echo(fmt_server(s))
            server_names.append(s.name)
    if unowned_servers:
        click.echo(success(f"{len(owned_servers)} unowned servers found:"))
        for s in unowned_servers:
            click.echo(fmt_server(s))
            server_names.append(s.name)

    return click.prompt(
        title("Select default server:"),
        type=Choice(server_names),
        show_default=True,
    )


def pick_server(account: MyPlexAccount):
    servers = account.resources()
    if not servers:
        return None

    if len(servers) == 1:
        return servers[0]

    server_name = prompt_server(servers)

    # Sanity check, even the user can't choose invalid resource
    server = account.resource(server_name)
    if server:
        return server

    return None


def choose_server(account: MyPlexAccount):
    while True:
        try:
            server = pick_server(account)
            # Connect to obtain baseUrl
            click.echo(title(f"Attempting to connect to {server.name}. This may take time and print some errors."))
            plex = server.connect()
            # Validate connection again, the way we connect
            plex = PlexServer(token=server.accessToken, baseurl=plex._baseurl)
            return [server, plex]
        except NotFound as e:
            click.secho(f"{e}, Try another server, {type(e)}")


@click.command()
@click.option("--username", help="Plex login", default=CONFIG["PLEX_USERNAME"])
@click.option("--password", help="Plex password")
def plex_login(username, password):
    """
    Log in to Plex Account to obtain Access Token. Optionally can use managed user on servers that you own.
    """

    if CONFIG["PLEX_TOKEN"]:
        if not click.confirm(PROMPT_PLEX_RELOGIN, default=True):
            return

    account = myplex_login(username, password)
    click.echo(success("Login to MyPlex was successful!"))

    [server, plex] = choose_server(account)
    click.echo(success(f"Connection to {plex.friendlyName} established successfully!"))

    token = server.accessToken
    user = username
    if server.owned:
        managed_user = choose_managed_user(account)
        if managed_user:
            user = managed_user
            token = account.user(managed_user).get_token(plex.machineIdentifier)

    CONFIG["PLEX_USERNAME"] = user
    CONFIG["PLEX_TOKEN"] = token
    CONFIG["PLEX_BASEURL"] = plex._baseurl
    CONFIG["PLEX_FALLBACKURL"] = "http://localhost:32400"
    CONFIG.save()

    click.echo(SUCCESS_MESSAGE)
