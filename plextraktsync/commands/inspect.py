from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote_plus

from humanize import naturalsize
from plexapi.utils import millisecondToHumanstr
from rich.markup import escape

from plextraktsync.factory import factory
from plextraktsync.plex.PlexId import PlexId
from plextraktsync.util.expand_id import expand_plexid

if TYPE_CHECKING:
    from plextraktsync.media.Media import Media
    from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem


def inspect_media(plex_id: PlexId):
    plex = plex_id.plex
    mf = factory.media_factory
    print = factory.print

    print("")
    pm: PlexLibraryItem = plex.fetch_item(plex_id)
    if not pm:
        print(f"Inspecting {plex_id}: Not found from {plex}")
        return

    print(f"Inspecting {plex_id}: {pm}")

    print("--- Plex")
    if pm.library:
        print(f"Library: {pm.library.title}")

    print(f"Plex Web URL: {pm.web_url}")
    if pm.discover_url:
        print(f"Discover URL: {pm.discover_url}")

    media = pm.item
    print(f"Title: {media.title}")
    if media.type == "movie" and pm.edition_title:
        print(f"Edition Title: {pm.edition_title}")
    if pm.has_media:
        print(f"Media.Duration: {pm.duration}")
    print(f"Media.Type: '{media.type}'")
    print(f"Media.Guid: '{media.guid}'")
    if not pm.is_legacy_agent:
        print(f"Media.Guids: {media.guids}")

    if not pm.is_discover and media.type in ["episode", "movie"]:
        audio = pm.audio_streams[0]
        print(f"Audio: '{audio.audioChannelLayout}', '{audio.displayTitle}'")

        video = pm.video_streams[0]
        print(f"Video: '{video.codec}'")

        print("Subtitles:")
        for index, subtitle in enumerate(pm.subtitle_streams, start=1):
            print(
                f"  Subtitle {index}: ({subtitle.language}) {subtitle.title}"
                f" (codec: {subtitle.codec}, selected: {subtitle.selected}, transient: {subtitle.transient})"
            )

        print("Parts:")
        pm.item.reload(checkFiles=True)
        for index, part in enumerate(pm.parts, start=1):
            size = naturalsize(part.size, binary=True)
            file_link = f"[link=file://{quote_plus(part.file)}]{escape(part.file)}[/link]"
            print(f"  Part {index} (exists: {part.exists}): {file_link} {size}")

        print("Markers:")
        for marker in pm.markers:
            start = millisecondToHumanstr(marker.start)
            end = millisecondToHumanstr(marker.end)
            print(f"  {marker.type}: {start} - {end}")

    print("Guids:")
    for guid in pm.guids:
        print(f"  Guid: {guid.provider_link}, Id: {guid.id}, Provider: '{guid.provider}'")

    print(f"Metadata: {pm.to_json()}")
    print(f"Played on Plex: {pm.is_watched}")
    print(f"Plex Play Date: {pm.seen_date}")

    history = plex.history(media, device=True, account=True) if not pm.is_discover else []
    print("Plex play history:")
    for h in history:
        d = h.device
        if not d:
            dn = f"deviceId {h.deviceID}"
        elif d.name == "" and d.platform == "":
            # "local" for offline plays
            dn = h.device.clientIdentifier
        else:
            dn = f"{d.name} with {d.platform}"
        if h.account:
            viewer = h.account.name
        else:
            viewer = f"accountId {h.accountID}"
        print(f"- {h.viewedAt} {h}: by {viewer} on {dn}")

    print("--- Trakt")
    m: Media = mf.resolve_any(pm)
    if not m:
        print("Trakt: No match found")
        return

    print(f"Trakt: {m.trakt_url}")
    print(f"Plex Rating: {m.plex_rating}")
    print(f"Trakt Rating: {m.trakt_rating}")
    if pm.has_media:
        print(f"Watched on Trakt: {m.watched_on_trakt}")
        print(f"Collected on Trakt: {m.is_collected}")


def inspect(inputs: list[str]):
    print = factory.print
    print(f"PlexTraktSync [{factory.version.full_version}]")

    for plex_id in expand_plexid(inputs):
        inspect_media(plex_id)
