import click
from plexapi.server import PlexServer
from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.database import PlexDatabase, Database
from plex_trakt_sync.media import MediaFactory
from plex_trakt_sync.plex_api import PlexApi
from plex_trakt_sync.trakt_api import TraktApi
from plex_trakt_sync.version import git_version_info


@click.command()
@click.argument('input')
def inspect(input):
    """
    Inspect details of an object
    """

    git_version = git_version_info() or 'Unknown version'
    print(f"PlexTraktSync inspect [{git_version}]")

    url = CONFIG["PLEX_BASEURL"]
    token = CONFIG["PLEX_TOKEN"]
    server = PlexServer(url, token)
    plex = PlexApi(server)
    trakt = TraktApi()
    mf = MediaFactory(plex=plex, trakt=trakt)

    if input.isnumeric():
        input = int(input)

    m = plex.fetch_item(input)
    print(f"Inspecting: {m}")

    media = m.item
    print(f"Guid: '{media.guid}'")
    print(f"Guids: {media.guids}")

    if media.type in ["episode", "movie"]:
        audio = media.media[0].parts[0].audioStreams()[0]
        print(f"Audio: '{audio.audioChannelLayout}', '{audio.displayTitle}'")

        video = media.media[0].parts[0].videoStreams()[0]
        print(f"Video: '{video.codec}'")

    print(f"Provider: {m.provider}")
    print(f"Id: {m.id}")

    try:
        tm = trakt.find_by_media(m)
        print(f"Trakt match: {tm}")
    except Exception as e:
        print(f"Error: {e}")

    mi = mf.resolve(m)
    print(f"Trakt watched at: {mi.trakt_last_watched_at}")

    if input == 6114:
        db = PlexDatabase(Database('com.plexapp.plugins.library.db'))
        db.mark_watched(mi, mi.trakt_last_watched_at)
