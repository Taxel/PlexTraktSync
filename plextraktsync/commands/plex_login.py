from __future__ import annotations

from functools import partial
from os import environ
from typing import TYPE_CHECKING

from click import ClickException
from InquirerPy import get_style, inquirer
from InquirerPy.base import Choice
from InquirerPy.separator import Separator
from plexapi.exceptions import BadRequest, NotFound, Unauthorized
from plexapi.myplex import MyPlexAccount

from plextraktsync.config.ServerConfig import ServerConfig
from plextraktsync.decorators.flatten import flatten_list
from plextraktsync.factory import factory
from plextraktsync.style import comment, error, prompt, success, title
from plextraktsync.util.local_url import local_url
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

if TYPE_CHECKING:
    from typing import List

    from plexapi.myplex import MyPlexResource, ResourceConnection

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

print = factory.print


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
        username = Prompt.ask(PROMPT_PLEX_USERNAME, default=username)
        print(NOTICE_2FA_PASSWORD, highlight=False)
        password = Prompt.ask(PROMPT_PLEX_PASSWORD, password=True, default=password, show_default=False)
        try:
            return MyPlexAccount(username, password)
        except Unauthorized as e:
            print(error(f"Log in to Plex failed: '{e}', Try again."), highlight=False)
        except BadRequest as e:
            print(error(f"Log in to Plex failed: '{e}'"), highlight=False)
            exit(1)


def choose_managed_user(account: MyPlexAccount):
    users = [u.title for u in account.users() if u.home]
    if not users:
        return None

    print(success("Managed user(s) found:"))
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


def format_server(s):
    lines = []
    product = f"{s.product}/{s.productVersion}"
    platform = f"{s.device}: {s.platform}/{s.platformVersion}"
    lines.append(f"{s.name}: Last seen: {str(s.lastSeenAt)}, Server: {product} on {platform}")
    c: ResourceConnection
    for c in s.connections:
        lines.append(f"    {c.uri}")

    return Choice(value=s.name, name="\n    ".join(lines))


def prompt_server(servers: List[MyPlexResource]):
    owned_servers = [s for s in servers if s.owned]
    unowned_servers = [s for s in servers if not s.owned]
    sorter = partial(sorted, key=lambda s: s.lastSeenAt, reverse=True)

    server_names = []
    if owned_servers:
        server_names.append(Separator("Owned servers"))
        for s in sorter(owned_servers):
            server_names.append(format_server(s))
    if unowned_servers:
        server_names.append(Separator("Unowned servers"))
        for s in sorter(unowned_servers):
            server_names.append(format_server(s))

    print()
    return inquirer.rawlist(
        message="Select default server:",
        choices=server_names,
        default=None,
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
            print()
            print(
                title(
                    f"Attempting to connect to {server.name}. This may take time and print some errors."
                )
            )
            print(title("Server connections:"))
            for c in server.connections:
                print(f"    {c.uri}")
            print()
            plex = server.connect()
            return [server, plex]
        except NotFound as e:
            print(Panel.fit(f"{e}. Try another server", padding=1, title="[b red]ERROR", border_style="red"))


def plex_login_autoconfig():
    username = environ.get("PLEX_USERNAME", CONFIG["PLEX_USERNAME"])
    password = environ.get("PLEX_PASSWORD", None)
    login(username, password)


def plex_login(username, password):
    login(username, password)


def login(username: str, password: str):
    if factory.has_plex_token:
        if not Confirm.ask(PROMPT_PLEX_RELOGIN, default=True):
            return

    account = myplex_login(username, password)
    print(Panel.fit("Login to MyPlex was successful", title="Plex Login",
                    title_align="left", padding=1, border_style="bright_blue"))

    [server, plex] = choose_server(account)
    print(success(f"Connection to {plex.friendlyName} established successfully!"))

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

    print(SUCCESS_MESSAGE)
