from urllib.parse import quote_plus

from plextraktsync.console import print
from plextraktsync.factory import factory
from plextraktsync.media import Media
from plextraktsync.plex_api import PlexLibraryItem
from plextraktsync.util.expand_id import expand_id
from plextraktsync.version import version


def inspect_media(id):
    plex = factory.plex_api
    mf = factory.media_factory

    print("")
    pm: PlexLibraryItem = plex.fetch_item(id)
    if not pm:
        print(f"Inspecting {id}: Not found")
        return

    print(f"Inspecting {id}: {pm}")
    if pm.library:
        print(f"Library: {pm.library.title}")

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
        print("Trakt: No match found")
        return

    print(f"Trakt: {m.trakt_url}")
    print(f"Plex Rating: {m.plex_rating}")
    print(f"Trakt Rating: {m.trakt_rating}")
    print(f"Watched on Plex: {m.watched_on_plex}")
    if pm.has_media:
        print(f"Watched on Trakt: {m.watched_on_trakt}")
        print(f"Collected on Trakt: {m.is_collected}")

    print("Plex play history:")
    for h in m.plex_history(device=True, account=True):
        print(
            f"- {h.viewedAt} {h}: by {h.account.name} on {h.device.name} with {h.device.platform}"
        )


def inspect(input):
    print(f"PlexTraktSync [{version()}]")

    for id in expand_id(input):
        inspect_media(id)
