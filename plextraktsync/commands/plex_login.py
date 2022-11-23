from datetime import datetime, timedelta
from functools import partial
from os import environ
from typing import List

import click
from click import ClickException
from InquirerPy import get_style, inquirer
from plexapi.exceptions import BadRequest, NotFound, Unauthorized
from plexapi.myplex import MyPlexAccount, MyPlexResource, ResourceConnection

from plextraktsync.config.ServerConfig import ServerConfig
from plextraktsync.decorators.flatten import flatten_list
from plextraktsync.factory import factory
from plextraktsync.style import (comment, disabled, error, highlight, prompt,
                                 success, title)
from plextraktsync.util.local_url import local_url

PROMPT_PLEX_PASSWORD = prompt("Please enter your Plex password")
PROMPT_PLEX_USERNAME = prompt("Please enter your Plex username or e-mail")
PROMPT_PLEX_RELOGIN = prompt(
    "You already have Plex Access Token, do you want to log in again?"
)
SUCCESS_MESSAGE = success(
    "Plex Media Server Authentication Token and base URL have been added to servers.yml"
)
NOTICE_2FA_PASSWORD = comment(
    "If you have 2 Factor Authentication enabled on Plex "
    "you can append the code to your password below (eg. passwordCODE)"
)
CONFIG = factory.config

style = get_style(
    {
        "questionmark": "hidden",
        "question": "ansiyellow",
        "pointer": "fg:ansiblack bg:ansiyellow",
    }
)


@flatten_list
def server_urls(server: MyPlexResource):
    """
    Return urls to connect to specific server
    """

    # https://github.com/pkkid/python-plexapi/blob/3d3f9da5012428f5d703cf9f8e95f6aa10673ea6/plexapi/myplex.py#L1309-L1314
    connections = server.preferred_connections(
        None,
        locations=server.DEFAULT_LOCATION_ORDER,
        schemes=server.DEFAULT_SCHEME_ORDER
    )
    yield from connections
    yield local_url()


def myplex_login(username, password):
    while True:
        username = click.prompt(PROMPT_PLEX_USERNAME, type=str, default=username)
        click.echo(NOTICE_2FA_PASSWORD)
        password = click.prompt(
            PROMPT_PLEX_PASSWORD,
            type=str,
            default=password,
            hide_input=True,
            show_default=False,
        )
        try:
            return MyPlexAccount(username, password)
        except Unauthorized as e:
            click.echo(error(f"Log in to Plex failed: {e}, Try again."))
        except BadRequest as e:
            click.echo(error(f"Log in to Plex failed: {e}"))
            exit(1)


def choose_managed_user(account: MyPlexAccount):
    users = [u.title for u in account.users() if u.home]
    if not users:
        return None

    click.echo(success("Managed user(s) found:"))
    users = sorted(users)
    users.insert(0, account.username)
    user = inquirer.select(
        message="Select the user you would like to use:",
        choices=users,
        default=None,
        style=style,
        qmark="",
        pointer=">",
    ).execute()

    if user == account.username:
        return None

    # Sanity check, even the user can't input invalid user
    user_account = account.user(user)
    if user_account:
        return user

    return None


def prompt_server(servers: List[MyPlexResource]):
    old_age = datetime.now() - timedelta(weeks=1)

    def fmt_server(s):
        if s.lastSeenAt < old_age:
            decorator = disabled
        else:
            decorator = comment

        product = decorator(f"{s.product}/{s.productVersion}")
        platform = decorator(f"{s.device}: {s.platform}/{s.platformVersion}")
        click.echo(
            f"- {highlight(s.name)}: [Last seen: {decorator(str(s.lastSeenAt))}, Server: {product} on {platform}]"
        )
        c: ResourceConnection
        for c in s.connections:
            click.echo(f"    {c.uri}")

    owned_servers = [s for s in servers if s.owned]
    unowned_servers = [s for s in servers if not s.owned]
    sorter = partial(sorted, key=lambda s: s.lastSeenAt)

    server_names = []
    if owned_servers:
        click.echo(success(f"{len(owned_servers)} owned servers found:"))
        for s in sorter(owned_servers):
            fmt_server(s)
            server_names.append(s.name)
    if unowned_servers:
        click.echo(success(f"{len(unowned_servers)} unowned servers found:"))
        for s in sorter(unowned_servers):
            fmt_server(s)
            server_names.append(s.name)

    return inquirer.select(
        message="Select default server:",
        choices=sorted(server_names),
        default=None,
        style=style,
        qmark="",
        pointer=">",
    ).execute()


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
            if not server:
                raise ClickException("Unable to find server from Plex account")

            # Connect to obtain baseUrl
            click.echo(
                title(
                    f"Attempting to connect to {server.name}. This may take time and print some errors."
                )
            )
            click.echo(title("Server connections:"))
            for c in server.connections:
                click.echo(f"    {c.uri}")
            plex = server.connect()
            return [server, plex]
        except NotFound as e:
            click.secho(f"{e}, Try another server, {type(e)}")


def has_plex_token():
    return factory.has_plex_token


def plex_login_autoconfig():
    username = environ.get("PLEX_USERNAME", CONFIG["PLEX_USERNAME"])
    password = environ.get("PLEX_PASSWORD", None)
    login(username, password)


def plex_login(username, password):
    login(username, password)


def login(username: str, password: str):
    if has_plex_token():
        if not click.confirm(PROMPT_PLEX_RELOGIN, default=True):
            return

    account = myplex_login(username, password)
    click.echo(success("Login to MyPlex was successful!"))

    [server, plex] = choose_server(account)
    click.echo(success(f"Connection to {plex.friendlyName} established successfully!"))

    token = server.accessToken
    user = account.username
    plex_owner_token = plex_account_token = ""
    if server.owned:
        managed_user = choose_managed_user(account)
        if managed_user:
            user = managed_user
            plex_owner_token = token
            token = account.user(managed_user).get_token(plex.machineIdentifier)
    else:
        plex_account_token = account._token

    sc = ServerConfig()
    sc.add_server(
        name=server.name,
        token=token,
        urls=server_urls(server),
    )
    sc.save()

    CONFIG["PLEX_OWNER_TOKEN"] = plex_owner_token
    CONFIG["PLEX_ACCOUNT_TOKEN"] = plex_account_token
    CONFIG["PLEX_USERNAME"] = user
    CONFIG["PLEX_SERVER"] = server.name
    CONFIG.save()

    click.echo(SUCCESS_MESSAGE)
