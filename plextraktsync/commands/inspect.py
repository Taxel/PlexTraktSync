import click

from plextraktsync.factory import factory
from plextraktsync.version import version


def print_watched_shows():
    from rich.table import Table

    from plextraktsync.console import console

    trakt = factory.trakt_api()

    table = Table(show_header=True, header_style="bold magenta", title="Watched shows on Trakt")
    table.add_column("Id", style="dim", width=6)
    table.add_column("Slug")
    table.add_column("Seasons", justify="right")
    for show_id, progress in sorted(trakt.watched_shows.shows.items()):
        id = f"[link=https://trakt.tv/shows/{show_id}]{show_id}[/]"
        slug = f"[link=https://trakt.tv/shows/{progress.slug}]{progress.slug}[/]"
        table.add_row(id, slug, str(len(progress.seasons)))

    console.print(table)


def inspect_media(id):
    plex = factory.plex_api()
    mf = factory.media_factory()

    print("")
    pm = plex.fetch_item(id)
    if not pm:
        print(f"Inspecting {id}: Not found")
        return

    print(f"Inspecting {id}: {pm}")

    url = plex.media_url(pm)
    print(f"URL: {url}")

    media = pm.item
    print(f"Media.Type: {media.type}")
    print(f"Media.Guid: '{media.guid}'")
    if not pm.is_legacy_agent:
        print(f"Media.Guids: {media.guids}")

    if media.type in ["episode", "movie"]:
        audio = pm.audio_streams[0]
        print(f"Audio: '{audio.audioChannelLayout}', '{audio.displayTitle}'")

        video = pm.video_streams[0]
        print(f"Video: '{video.codec}'")

        print("Parts:")
        for index, part in enumerate(pm.parts, start=1):
            print(f"  Part {index}: {part.file}")

    print("Guids:")
    for guid in pm.guids:
        print(f"  Guid: {guid}, Id: {guid.id}, Provider: {guid.provider}")

    print(f"Metadata: {pm.to_json()}")

    m = mf.resolve_any(pm)
    if not m:
        return

    # fetch show property for watched_on_trakt
    if m.is_episode:
        ps = plex.fetch_item(m.plex.item.grandparentRatingKey)
        ms = mf.resolve_any(ps)
        m.show = ms

    print(f"Trakt: {m.trakt_url}")
    print(f"Plex Rating: {m.plex_rating}")
    print(f"Trakt Rating: {m.trakt_rating}")
    print(f"Watched on Plex: {m.watched_on_plex}")
    print(f"Watched on Trakt: {m.watched_on_trakt}")

    print("Plex play history:")
    for h in m.plex_history(device=True, account=True):
        print(f"- {h.viewedAt} by {h.account.name} on {h.device.name} with {h.device.platform}")


@click.command()
@click.argument('input', nargs=-1)
@click.option(
    "--watched-shows",
    type=bool,
    default=False,
    is_flag=True,
    help="Print Trakt watched_shows and exit"
)
def inspect(input, watched_shows: bool):
    """
    Inspect details of an object
    """

    print(f"PlexTraktSync [{version()}]")

    if watched_shows:
        print_watched_shows()
        return

    for id in input:
        if id.isnumeric():
            id = int(id)
        inspect_media(id)
