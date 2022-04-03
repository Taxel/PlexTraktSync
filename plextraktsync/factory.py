from deprecated import deprecated

from plextraktsync.decorators.memoize import memoize
from plextraktsync.rich_addons import RichHighlighter


class Factory:
    @memoize
    def trakt_api(self):
        from plextraktsync.trakt_api import TraktApi

        config = self.run_config()
        trakt = TraktApi(batch_delay=config.batch_delay)

        return trakt

    @memoize
    def plex_api(self):
        from plextraktsync.plex_api import PlexApi

        server = self.plex_server()
        plex = PlexApi(server)

        return plex

    @memoize
    def media_factory(self):
        from plextraktsync.media import MediaFactory

        trakt = self.trakt_api()
        plex = self.plex_api()
        mf = MediaFactory(plex, trakt)

        return mf

    @memoize
    def plex_server(self):
        from plextraktsync.plex_server import get_plex_server

        return get_plex_server()

    @memoize
    def session(self):
        from requests_cache import CachedSession

        config = self.config()
        trakt_cache = config["cache"]["path"]
        session = CachedSession(trakt_cache)

        return session

    @memoize
    @deprecated("Use session instead")
    def requests_cache(self):
        import requests_cache

        config = self.config()
        trakt_cache = config["cache"]["path"]

        requests_cache.install_cache(trakt_cache)

        return requests_cache

    @memoize
    def sync(self):
        from plextraktsync.sync import Sync

        config = self.config()

        return Sync(config)

    @memoize
    def progressbar(self, enabled=True):
        if enabled:
            import warnings
            from functools import partial

            from tqdm import TqdmExperimentalWarning
            from tqdm.rich import tqdm

            from plextraktsync.console import console

            warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)

            return partial(tqdm, options={'console': console})

        return None

    @memoize
    def run_config(self):
        from plextraktsync.config import RunConfig

        config = RunConfig()

        return config

    @memoize
    def walk_config(self):
        from plextraktsync.walker import WalkConfig

        wc = WalkConfig()

        return wc

    @memoize
    def plex_audio_codec(self):
        from plextraktsync.plex_api import PlexAudioCodec

        return PlexAudioCodec()

    @memoize
    def walker(self):
        from plextraktsync.walker import Walker

        config = self.run_config()
        walk_config = self.walk_config()
        plex = self.plex_api()
        trakt = self.trakt_api()
        mf = self.media_factory()
        pb = self.progressbar(config.progressbar)
        w = Walker(plex=plex, trakt=trakt, mf=mf, config=walk_config, progressbar=pb)

        return w

    @memoize
    def console_logger(self):
        from rich.logging import RichHandler

        from plextraktsync.console import console

        handler = RichHandler(console=console, show_time=False, show_path=False, highlighter=RichHighlighter())

        return handler

    @memoize
    def config(self):
        from plextraktsync.config import CONFIG

        return CONFIG


factory = Factory()
