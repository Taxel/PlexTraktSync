from urllib.parse import quote_plus

from plextraktsync.console import print
from plextraktsync.factory import factory
from plextraktsync.media import Media
from plextraktsync.plex_api import PlexLibraryItem
from plextraktsync.version import version


def print_watched_shows():
    from rich.table import Table

    trakt = factory.trakt_api()

    table = Table(
        show_header=True, header_style="bold magenta", title="Watched shows on Trakt"
    )
    table.add_column("Id", style="dim", width=6)
    table.add_column("Slug")
    table.add_column("Seasons", justify="right")
    for show_id, progress in sorted(trakt.watched_shows.shows.items()):
        id = f"[link=https://trakt.tv/shows/{show_id}]{show_id}[/]"
        slug = f"[link=https://trakt.tv/shows/{progress.slug}]{progress.slug}[/]"
        table.add_row(id, slug, str(len(progress.seasons)))

    print(table)


def inspect_media(id):
    plex = factory.plex_api()
    mf = factory.media_factory()

    print("")
    pm: PlexLibraryItem = plex.fetch_item(id)
    if not pm:
        print(f"Inspecting {id}: Not found")
        return

    print(f"Inspecting {id}: {pm}")

    url = plex.media_url(pm)
    print(f"URL: {url}")

    media = pm.item
    print(f"Title: {media.title}")
    if media.type == 'movie' and media.editionTitle:
        print(f"Edition Title: {media.editionTitle}")
    if pm.has_media:
        print(f"Media.Duration: {pm.duration}")
    print(f"Media.Type: '{media.type}'")
    print(f"Media.Guid: '{media.guid}'")
    if not pm.is_legacy_agent:
        print(f"Media.Guids: {media.guids}")

    if media.type in ["episode", "movie"]:
        audio = pm.audio_streams[0]
        print(f"Audio: '{audio.audioChannelLayout}', '{audio.displayTitle}'")

        video = pm.video_streams[0]
        print(f"Video: '{video.codec}'")

        print("Subtitles:")
        for index, subtitle in enumerate(pm.subtitle_streams, start=1):
            print(f"  Subtitle {index}: ({subtitle.language}) {subtitle.title} (codec: {subtitle.codec}, selected: {subtitle.selected}, transient: {subtitle.transient})")

        print("Parts:")
        for index, part in enumerate(pm.parts, start=1):
            print(f"  Part {index}: [link=file://{quote_plus(part.file)}]{part.file}[/link]")

    print("Guids:")
    for guid in pm.guids:
        print(f"  Guid: {guid}, Id: {guid.id}, Provider: '{guid.provider}'")

    print(f"Metadata: {pm.to_json()}")

    m: Media = mf.resolve_any(pm)
    if not m:
        return

    print(f"Trakt: {m.trakt_url}")
    print(f"Plex Rating: {m.plex_rating}")
    print(f"Trakt Rating: {m.trakt_rating}")
    print(f"Watched on Plex: {m.watched_on_plex}")
    if pm.has_media:
        print(f"Watched on Trakt: {m.watched_on_trakt}")

    print("Plex play history:")
    for h in m.plex_history(device=True, account=True):
        print(
            f"- {h.viewedAt} {h}: by {h.account.name} on {h.device.name} with {h.device.platform}"
        )


def inspect(input, no_cache: bool, watched_shows: bool):
    print(f"PlexTraktSync [{version()}]")

    factory.run_config().update(
        no_cache=no_cache,
    )

    if watched_shows:
        print_watched_shows()
        return

    from plextraktsync.util.expand_id import expand_id
    for id in expand_id(input):
        inspect_media(id)
