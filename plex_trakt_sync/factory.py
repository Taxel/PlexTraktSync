from plex_trakt_sync.decorators import memoize


class Factory:
    @memoize
    def trakt_api(self, batch_size=None):
        from plex_trakt_sync.trakt_api import TraktApi

        trakt = TraktApi(batch_size=batch_size)

        return trakt

    @memoize
    def plex_api(self):
        from plex_trakt_sync.config import CONFIG
        from plex_trakt_sync.plex_api import PlexApi
        from plexapi.server import PlexServer

        url = CONFIG["PLEX_BASEURL"]
        token = CONFIG["PLEX_TOKEN"]
        server = PlexServer(url, token)
        plex = PlexApi(server)

        return plex

    @memoize
    def media_factory(self):
        from plex_trakt_sync.media import MediaFactory

        trakt = self.trakt_api()
        plex = self.plex_api()
        mf = MediaFactory(plex, trakt)

        return mf

    @memoize
    def plex_server(self):
        from plex_trakt_sync.plex_server import get_plex_server

        return get_plex_server()


factory = Factory()
