import click
from click import Choice
from plexapi.exceptions import Unauthorized
from plexapi.myplex import MyPlexAccount
from plex_trakt_sync.config import CONFIG

PROMPT_PLEX_PASSWORD = click.style("Please enter your Plex password", fg="yellow")
PROMPT_PLEX_USERNAME = click.style("Please enter your Plex username", fg="yellow")
PROMPT_PLEX_RELOGIN = click.style("You already logged in to Plex, do you want to log in again?", fg="yellow")
PROMPT_MANAGED_USER = click.style("Do you want to use managed user instead of main account?", fg="yellow")


def myplex_login(username, password):
    while True:
        username = click.prompt(PROMPT_PLEX_USERNAME, type=str, default=username)
        password = click.prompt(PROMPT_PLEX_PASSWORD, type=str, default=password, hide_input=True, show_default=False)
        try:
            return MyPlexAccount(username, password)
        except Unauthorized as e:
            click.secho(f"Logging failed: {e} Try again.", fg="red")


def choose_managed_user(account: MyPlexAccount):
    users = [u.title for u in account.users() if u.friend]
    if not users:
        return None

    click.secho("Managed user(s) found:", fg="green")
    users = sorted(users)
    for user in users:
        click.echo(f"- {user}")

    if not click.confirm(PROMPT_MANAGED_USER):
        return None

    # choice = prompt_choice(users)
    user = click.prompt(
        click.style("Please select:", fg="yellow"),
        type=Choice(users),
        show_default=True,
    )

    # Sanity check, even the user can't input invalid user
    user_account = account.user(user)
    if user_account:
        return user

    return None


@click.command()
@click.option("--username", help="Plex login", default=CONFIG["PLEX_USERNAME"])
@click.option("--password", help="Plex password")
def plex_login(username, password):
    """
    Log in to Plex Account
    """

    if CONFIG["PLEX_TOKEN"]:
        if not click.confirm(PROMPT_PLEX_RELOGIN, default=True):
            return

    account = myplex_login(username, password)
    click.secho("Login success!", fg="green")

    managed_user = choose_managed_user(account)
    if managed_user:
        user = managed_user
        token = account.user(managed_user).get_token(account.machineIdentifier)
    else:
        user = username
        token = account.machineIdentifier

    baseurl = account._baseurl

    print(f"User={user}, token={token}, {baseurl}")
