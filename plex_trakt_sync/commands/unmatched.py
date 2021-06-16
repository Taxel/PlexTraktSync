import click

from plex_trakt_sync.commands.login import ensure_login
from plex_trakt_sync.factory import factory
from plex_trakt_sync.walker import Walker


@click.command()
def unmatched():
    """
    List media that has no match in Plex
    """

    ensure_login()
    plex = factory.plex_api()
    mf = factory.media_factory()
    walker = Walker(plex, mf, progressbar=click.progressbar)

    if not walker.is_valid():
        click.echo("Nothing to scan, this is likely due conflicting options given.")
        return

    walker.walk_details(print=click.echo)

    failed = []
    for pm in walker.get_plex_movies():
        movie = mf.resolve_any(pm)
        if not movie:
            failed.append(pm)
            continue

    for pm in failed:
        print(f"Failed: {pm}")
