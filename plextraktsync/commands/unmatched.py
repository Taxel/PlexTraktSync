import click

from plextraktsync.commands.login import ensure_login
from plextraktsync.factory import factory
from plextraktsync.walker import WalkConfig, Walker


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

    config = factory.run_config().update(progressbar=not no_progress_bar)
    ensure_login()
    plex = factory.plex_api()
    trakt = factory.trakt_api()
    mf = factory.media_factory()
    pb = factory.progressbar(config.progressbar)
    wc = WalkConfig()
    walker = Walker(plex, trakt, mf, wc, progressbar=pb)

    if not wc.is_valid():
        click.echo("Nothing to scan, this is likely due conflicting options given.")
        return

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
