from plex_trakt_sync.main import get_plex_server


class PlexApi:
    """
    Plex API class abstracting common data access and dealing with requests cache.
    """

    @property
    def plex_server(self):
        return get_plex_server()
