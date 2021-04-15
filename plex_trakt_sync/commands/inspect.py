import click
from plexapi.server import PlexServer
from plex_trakt_sync.config import CONFIG
from plex_trakt_sync.plex_api import PlexApi
from plex_trakt_sync.trakt_api import TraktApi


@click.command()
@click.argument('input')
def inspect(input):
    """
    Inspect details of an object
    """

    url = CONFIG["PLEX_BASEURL"]
    token = CONFIG["PLEX_TOKEN"]
    server = PlexServer(url, token)
    plex = PlexApi(server)
    trakt = TraktApi()

    if input.isnumeric():
        input = int(input)

    m = plex.fetch_item(input)
    print(f"Inspecting: {m}")

    media = m.item
    print(f"Guid: '{media.guid}'")
    print(f"Guids: {media.guids}")

    audio = media.media[0].parts[0].audioStreams()[0]
    print(f"Audio: '{audio.audioChannelLayout}', '{audio.displayTitle}'")

    video = media.media[0].parts[0].videoStreams()[0]
    print(f"Video: '{video.codec}'")

    print(f"Provider: {m.provider}")
    print(f"Id: {m.id}")

    try:
        if m.type == "episode":
            show = plex.fetch_item(media.grandparentRatingKey)
            print(f"Show: {show}")
            season = plex.fetch_item(media.parentRatingKey)
            print(f"Season: {season}")
            tm = trakt.find_episode(m, show)
        else:
            tm = trakt.find_by_media(m)
        print(f"Trakt match: {tm}")
    except Exception as e:
        print(f"Error: {e}")
