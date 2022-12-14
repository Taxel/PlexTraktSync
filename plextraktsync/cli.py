import sys
from functools import wraps
from os import environ

import click
from click import Abort
from click.exceptions import ClickException, Exit

from plextraktsync.factory import factory


def command():
    """
    Wrapper to lazy load commands when commands being executed only
    """

    def decorator(fn):
        @click.command()
        @wraps(fn)
        def wrap(*args, **kwargs):
            import importlib

            name = fn.__name__
            module = importlib.import_module(f".commands.{name}", package=__package__)
            cmd = getattr(module, name)

            try:
                cmd(*args, **kwargs)
            except RuntimeError as e:
                from click import ClickException

                raise ClickException(f"Error running {name} command: {str(e)}")

        return wrap

    return decorator


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Print version and exit")
@click.option("--no-cache", is_flag=True, help="Disable cache in for Trakt HTTP requests")
@click.option("--no-progressbar", is_flag=True, help="Disable progressbar")
@click.option("--batch-delay", default=5, show_default=True,
              help="Time in seconds between each collection batch submit to Trakt")
@click.option("--server", help="Plex Server name from servers.yml")
@click.pass_context
def cli(ctx,
        version: bool,
        no_cache: bool,
        no_progressbar: bool,
        batch_delay: int,
        server: str,
        ):
    """
    Plex-Trakt-Sync is a two-way-sync between trakt.tv and Plex Media Server
    """

    if version:
        from .version import version
        print(f"PlexTraktSync {version()}")
        return

    factory.run_config.update(
        cache=not no_cache,
        progressbar=not no_progressbar,
        batch_delay=batch_delay,
        server=server,
    )

    if not ctx.invoked_subcommand:
        logger = factory.logger
        logger.warning('plextraktsync without command is deprecated. Executing "plextraktsync sync"')
        sync()


@command()
@click.option(
    "--sort",
    type=click.Choice(["size", "date", "url"], case_sensitive=False),
    default="size",
    show_default=True,
    help="Sort mode",
)
@click.option(
    "--limit",
    type=int,
    default=20,
    show_default=True,
    help="Limit entries to be printed",
)
@click.option("--reverse", is_flag=True, default=False, help="Sort reverse")
@click.option("--expire", is_flag=True, default=False, help="Expire given url")
@click.argument("url", required=False)
def cache():
    """
    Manage and analyze Requests Cache.
    """
    pass


@command()
@click.option("--confirm", is_flag=True, help="Confirm the dangerous action")
@click.option("--dry-run", is_flag=True, help="Do not perform delete actions")
def clear_collections():
    """
    Clear Movies and Shows collections in Trakt
    """

    pass


@command()
def info():
    """
    Print application and environment version info
    """

    pass


@command()
@click.argument("input", nargs=-1)
def inspect():
    """
    Inspect details of an object
    """

    pass


@command()
def login():
    """
    Log in to Plex and Trakt if needed
    """
    pass


def env_plex_username():
    from plextraktsync.factory import factory
    config = factory.config()

    return environ.get("PLEX_USERNAME", config["PLEX_USERNAME"])


@command()
@click.option(
    "--username",
    help="Plex login",
    default=env_plex_username,
)
@click.option(
    "--password",
    help="Plex password",
    default=lambda: environ.get("PLEX_PASSWORD", None),
)
def plex_login():
    """
    Log in to Plex Account to obtain Access Token. Optionally can use managed user on servers that you own.
    """
    pass


@command()
@click.option("--library", help="Specify Library to use")
@click.option(
    "--show", "show", type=str, show_default=True, help="Sync specific show only"
)
@click.option(
    "--movie", "movie", type=str, show_default=True, help="Sync specific movie only"
)
@click.option(
    "--id",
    "ids",
    type=str,
    multiple=True,
    show_default=True,
    help="Sync specific item only",
)
@click.option(
    "--sync",
    "sync_option",
    type=click.Choice(["all", "movies", "tv", "shows"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Specify what to sync",
)
@click.option(
    "--server",
    type=str,
    help="Plex Server name from servers.yml",
)
@click.option(
    "--batch-delay",
    "batch_delay",
    type=int,
    help="Time in seconds between each collection batch submit to trakt",
)
@click.option(
    "--dry-run",
    "dry_run",
    type=bool,
    default=False,
    is_flag=True,
    help="Dry run: Do not make changes",
)
@click.option(
    "--no-progress-bar",
    "no_progress_bar",
    type=bool,
    default=False,
    is_flag=True,
    help="Don't output progress bars",
)
def sync():
    """
    Perform sync between Plex and Trakt
    """
    pass


@command()
def trakt_login():
    """
    Log in to Trakt Account to obtain Access Token.
    """
    pass


@command()
@click.option(
    "--no-progress-bar",
    "no_progress_bar",
    type=bool,
    default=False,
    is_flag=True,
    help="Don't output progress bars",
)
@click.option(
    "--local",
    type=bool,
    default=False,
    is_flag=True,
    help="Show only local files (no match in Plex)",
)
def unmatched():
    """
    List media that has no match in Trakt or Plex
    """

    pass


@command()
@click.option(
    "--server",
    type=str,
    help="Plex Server name from servers.yml",
)
def watch():
    """
    Listen to events from Plex
    """
    pass


@command()
@click.argument("input", nargs=-1)
def subdl():
    """
    Downloads subtitles to a local directory
    """
    pass


@command()
@click.option(
    "--pr",
    type=int,
    default=False,
    help="Install plextraktsync for specific Pull Request",
)
def self_update():
    """
    Update PlexTraktSync to the latest version using pipx

    \b
    $ plextraktsync self-update
    Updating PlexTraktSync to latest using pipx
    upgraded package plextraktsync from 0.15.3 to 0.18.5 (location: /Users/glen/.local/pipx/venvs/plextraktsync)
    """
    pass


@command()
def bug_report():
    """
    Create a pre-populated GitHub issue with information about your configuration
    """
    pass


@command()
@click.argument("input")
@click.option("--dry-run", is_flag=True, help="Do not perform actions that change data")
def imdb_import():
    """
    Import IMDB ratings from CSV file.

    See IMDB help how to export:

    \b
    - https://help.imdb.com/article/imdb/track-movies-tv/ratings-faq/G67Y87TFYYP6TWAV
    """
    pass


@command()
def watched_shows():
    """
    Print a table of watched shows
    """
    pass


@command()
def config():
    """
    Print user config for debugging and bug reports.
    """
    pass


cli.add_command(bug_report)
cli.add_command(cache)
cli.add_command(clear_collections)
cli.add_command(config)
cli.add_command(imdb_import)
cli.add_command(info)
cli.add_command(inspect)
cli.add_command(login)
cli.add_command(plex_login)
if factory.enable_self_update:
    cli.add_command(self_update)
cli.add_command(subdl)
cli.add_command(sync)
cli.add_command(trakt_login)
cli.add_command(unmatched)
cli.add_command(watch)
cli.add_command(watched_shows)


def main():
    try:
        exit_code = cli(standalone_mode=False)
    except ClickException as e:
        factory.cleanup.run()
        e.show()
        sys.exit(e.exit_code)
    except Abort:
        factory.cleanup.run()
        print("Aborted!")
        sys.exit(1)
    except Exit as e:
        raise ClickException(f"Exited with {e.exit_code}.")

    sys.exit(exit_code)
