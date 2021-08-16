import click
from tqdm import tqdm

from plex_trakt_sync.commands.login import ensure_login
from plex_trakt_sync.factory import factory
from plex_trakt_sync.walker import Walker


@click.option(
    "--no-progress-bar", "no_progress_bar",
    type=bool,
    default=False,
    is_flag=True,
    help="Don't output progress bars"
)
@click.command()
def unmatched(no_progress_bar: bool):
    """
    List media that has no match in Plex
    """

    ensure_login()
    plex = factory.plex_api()
    mf = factory.media_factory()
    pb = factory.progressbar(not no_progress_bar)
    walker = Walker(plex, mf, progressbar=pb)

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
        p = pm.item
        url = plex.media_url(pm)
        print("=" * 80)
        print(f"No match: {pm}")
        print(f"URL: {url}")
        print(f"Title: {p.title}")
        print(f"Year: {p.year}")
        print(f"Updated At: {p.updatedAt}")
        for l in p.locations:
            print(f"Location: {l}")

        print("")
