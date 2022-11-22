from os.path import exists

from plextraktsync.factory import factory
from plextraktsync.plex_api import PlexApi, PlexLibraryItem
from plextraktsync.util.expand_id import expand_id


def download(plex: PlexApi, pm: PlexLibraryItem):
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


def subdl(input):
    plex = factory.plex_api

    for id in expand_id(input):
        pm = plex.fetch_item(id)
        if not pm:
            continue
        download(plex, pm)
