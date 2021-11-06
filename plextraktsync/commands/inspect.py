import click

from plextraktsync.factory import factory
from plextraktsync.media import Media
from plextraktsync.version import git_version_info


def print_watched_shows():
    print("Watched shows on Trakt")
    trakt = factory.trakt_api()
    shows = trakt.watched_shows
    for show_id, progress in sorted(shows.shows.items()):
        print(f"- {show_id}: {progress.slug}, {len(progress.seasons)} seasons")


@click.command()
@click.argument('input', nargs=-1)
@click.option(
    "--watched-shows",
    type=bool,
    default=False,
    is_flag=True,
    help="Print Trakt watched_shows and exit"
)
def inspect(input, watched_shows):
    """
    Inspect details of an object
    """
    if watched_shows:
        print_watched_shows()
        return

    git_version = git_version_info() or 'Unknown version'
    print(f"PlexTraktSync inspect [{git_version}]")

    plex = factory.plex_api()
    mf = factory.media_factory()

    if input.isnumeric():
        input = int(input)

    pm = plex.fetch_item(input)
    print(f"Inspecting {input}: {pm}")

    url = plex.media_url(pm)
    print(f"URL: {url}")

    media = pm.item
    print(f"Media.Type: {media.type}")
    print(f"Media.Guid: '{media.guid}'")
    if not pm.is_legacy_agent:
        print(f"Media.Guids: {media.guids}")

    if media.type in ["episode", "movie"]:
        audio = media.media[0].parts[0].audioStreams()[0]
        print(f"Audio: '{audio.audioChannelLayout}', '{audio.displayTitle}'")

        video = media.media[0].parts[0].videoStreams()[0]
        print(f"Video: '{video.codec}'")

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
    print(f"Watched on Plex: {m.watched_on_plex}")
    print(f"Watched on Trakt: {m.watched_on_trakt}")

    print("Play history:")
    for h in m.plex_history(device=True, account=True):
        print(f"- {h.lastViewedAt} by {h.account.name} with {h.device.name} on {h.device.platform}")
