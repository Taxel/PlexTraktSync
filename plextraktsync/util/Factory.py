from __future__ import annotations

from typing import TYPE_CHECKING

from plextraktsync.decorators.cached_property import cached_property

if TYPE_CHECKING:
    from typing import List


class Factory:
    def invalidate(self, keys: List[str] = None):
        """
        Invalidate set of cached properties

        https://stackoverflow.com/a/63617398
        """
        for key in keys or []:
            try:
                del self.__dict__[key]
            except KeyError:
                pass

    @cached_property
    def version(self):
        from plextraktsync.util.Version import Version

        return Version()

    @cached_property
    def console(self):
        from plextraktsync.rich_addons import RichHighlighter
        from rich.console import Console

        return Console(highlighter=RichHighlighter())

    @cached_property
    def print(self):
        return self.console.print

    @cached_property
    def trakt_api(self):
        from plextraktsync.trakt.TraktApi import TraktApi

        return TraktApi()

    @cached_property
    def plex_api(self):
        from plextraktsync.plex.PlexApi import PlexApi

        server = self.plex_server
        plex = PlexApi(server)

        return plex

    @cached_property
    def media_factory(self):
        from plextraktsync.media import MediaFactory

        trakt = self.trakt_api
        plex = self.plex_api
        mf = MediaFactory(plex, trakt)

        return mf

    @cached_property
    def plex_server(self):
        from plextraktsync.factory import factory
        from plextraktsync.plex.PlexServerConnection import \
            PlexServerConnection

        server = self.server_config

        return PlexServerConnection(factory).connect(
            urls=server.urls,
            token=server.token,
        )

    @cached_property
    def has_plex_token(self):
        try:
            return self.server_config.token is not None
        except RuntimeError:
            return False

    @cached_property
    def server_config(self):
        from plextraktsync.config.ServerConfig import ServerConfig

        config = self.config
        run_config = self.run_config
        server_config = ServerConfig()
        server_name = run_config.server

        if server_name is None:
            # NOTE: the load() is needed because config["PLEX_SERVER"] may change during migrate() there.
            server_config.load()
            server_name = config["PLEX_SERVER"]

        return server_config.get_server(server_name)

    @cached_property
    def session(self):
        from requests_cache import CachedSession

        if self.run_config.cache:
            urls_expire_after = self.config.http_cache.urls_expire_after
        else:
            from requests_cache import DO_NOT_CACHE
            urls_expire_after = {
                "*": DO_NOT_CACHE,
            }

        return CachedSession(
            cache_name=self.config.cache_path,
            urls_expire_after=urls_expire_after,
        )

    @cached_property
    def sync(self):
        from plextraktsync.sync import Sync

        config = self.config
        plex = self.plex_api
        trakt = self.trakt_api

        return Sync(config, plex, trakt)

    @cached_property
    def progressbar(self):
        if not self.run_config.progressbar:
            return None

        import warnings
        from functools import partial

        from tqdm import TqdmExperimentalWarning
        from tqdm.rich import tqdm

        warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)

        # Monkeypatch https://github.com/tqdm/tqdm/pull/1395
        class Tqdm(tqdm):
            def close(self):
                if self.disable:
                    return
                self.display()
                super().close()

        return partial(Tqdm, options={'console': self.console})

    @cached_property
    def run_config(self):
        from plextraktsync.config.RunConfig import RunConfig

        config = RunConfig()

        return config

    @cached_property
    def walk_config(self):
        from plextraktsync.walker import WalkConfig

        wc = WalkConfig()

        return wc

    @cached_property
    def plex_audio_codec(self):
        from plextraktsync.plex.PlexAudioCodec import PlexAudioCodec

        return PlexAudioCodec()

    @cached_property
    def walker(self):
        from plextraktsync.walker import Walker

        walk_config = self.walk_config
        plex = self.plex_api
        trakt = self.trakt_api
        mf = self.media_factory
        pb = self.progressbar
        w = Walker(plex=plex, trakt=trakt, mf=mf, config=walk_config, progressbar=pb)

        return w

    @cached_property
    def enable_self_update(self):
        from plextraktsync.util.packaging import pipx_installed, program_name

        package = pipx_installed(program_name())

        return package is not None

    @cached_property
    def web_socket_listener(self):
        from plextraktsync.watch.WebSocketListener import WebSocketListener

        return WebSocketListener(plex=self.plex_server)

    @cached_property
    def watch_state_updater(self):
        from plextraktsync.watch.WatchStateUpdater import WatchStateUpdater

        return WatchStateUpdater(
            plex=self.plex_api,
            trakt=self.trakt_api,
            mf=self.media_factory,
            config=self.config,
        )

    @cached_property
    def logging(self):
        import logging

        from plextraktsync.logging import initialize

        config = self.config
        initialize(config)

        return logging

    @cached_property
    def logger(self):
        logger = self.logging.getLogger("PlexTraktSync")
        config = self.config
        loggers = [
            "PlexTraktSync",
            "PlexTraktSync.BackgroundTask",
            "PlexTraktSync.EventDispatcher",
            "PlexTraktSync.PlexServerConnection",
            "PlexTraktSync.ScrobblerProxy",
            "PlexTraktSync.Timer",
            "PlexTraktSync.TraktBatchWorker",
            "PlexTraktSync.WatchStateUpdater",
            "PlexTraktSync.WebSocketListener",
        ]
        loggers.extend(config["logging"]["filter_loggers"] or [])

        from plextraktsync.logger.filter import LoggerFilter
        filter = LoggerFilter(config["logging"]["filter"], logger)

        for name in loggers:
            self.logging.getLogger(name).addFilter(filter)

        return logger

    @cached_property
    def console_logger(self):
        from plextraktsync.rich_addons import RichHighlighter
        from rich.logging import RichHandler

        config = self.config
        handler = RichHandler(
            console=self.console,
            show_time=config.log_console_time,
            log_time_format='[%Y-%m-%d %X]',
            show_path=False,
            highlighter=RichHighlighter(),
        )

        return handler

    @cached_property
    def config(self):
        from plextraktsync.config.Config import Config

        def invalidate_plex_cache(key, value):
            self.invalidate(["has_plex_token", "server_config"])

        config = Config()
        config.add_listener(invalidate_plex_cache, ["PLEX_SERVER"])

        return config

    @cached_property
    def queue(self):
        from plextraktsync.queue.BackgroundTask import BackgroundTask
        from plextraktsync.queue.Queue import Queue
        from plextraktsync.queue.TraktBatchWorker import TraktBatchWorker
        from plextraktsync.queue.TraktMarkWatchedWorker import \
            TraktMarkWatchedWorker

        workers = [
            TraktBatchWorker(),
            TraktMarkWatchedWorker(),
        ]
        task = BackgroundTask(self.batch_delay_timer, *workers)
        queue = Queue(task)

        return queue

    @cached_property
    def batch_delay_timer(self):
        from plextraktsync.util.Timer import Timer

        return Timer(self.run_config.batch_delay) if self.run_config.batch_delay else None
