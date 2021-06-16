from plex_trakt_sync.decorators import memoize


class Factory:
    @memoize
    def trakt_api(self, batch_size=None):
        from plex_trakt_sync.trakt_api import TraktApi

        trakt = TraktApi(batch_size=batch_size)

        return trakt

    @memoize
    def plex_api(self):
        from plex_trakt_sync.plex_api import PlexApi

        server = self.plex_server()
        plex = PlexApi(server)

        return plex

    @memoize
    def media_factory(self, batch_size=None):
        from plex_trakt_sync.media import MediaFactory

        trakt = self.trakt_api(batch_size=batch_size)
        plex = self.plex_api()
        mf = MediaFactory(plex, trakt)

        return mf

    @memoize
    def plex_server(self):
        from plex_trakt_sync.plex_server import get_plex_server

        return get_plex_server()


factory = Factory()
