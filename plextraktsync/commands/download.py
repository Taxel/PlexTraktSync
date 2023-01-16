from __future__ import annotations

from os.path import exists
from typing import TYPE_CHECKING

from plextraktsync.factory import factory
from plextraktsync.util.expand_id import expand_id

if TYPE_CHECKING:
    from typing import List

    from plextraktsync.plex.PlexApi import PlexApi
    from plextraktsync.plex.PlexLibraryItem import PlexLibraryItem


def download_media(plex: PlexApi, pm: PlexLibraryItem):
    print(f"Download media for {pm}:")
    for index, part in enumerate(pm.parts, start=1):
        print(f"Downloading part {index}: {part.file}")
        plex.download(part, filename=part.file, showstatus=True)


def download_subtitles(plex: PlexApi, pm: PlexLibraryItem):
    print(f"Subtitles for {pm}:")
    for index, sub in enumerate(pm.subtitle_streams, start=1):
        print(
            f"  Subtitle {index}: ({sub.language}) {sub.title} (codec: {sub.codec}, selected: {sub.selected}, transient: {sub.transient})"
        )
        filename = f"{sub.id}. {f'{sub.language}.' if sub.language else ''}{sub.languageCode}.{sub.codec}"
        if not exists(filename):
            if not sub.key:
                print(f"  ERROR: Subtitle {index}: has no key: Not downloadable")
                continue

            plex.download(sub, filename=filename, showstatus=True)


def download(input: List[str], only_subs: bool):
    plex = factory.plex_api
    print = factory.print

    for id in expand_id(input):
        pm = plex.fetch_item(id)
        if not pm:
            print(f"Not found: {id}. Skipping")
            continue

        if not only_subs:
            download_media(plex, pm)

        download_subtitles(plex, pm)
