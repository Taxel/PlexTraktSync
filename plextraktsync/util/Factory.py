from __future__ import annotations

from functools import cached_property


class Factory:
    def invalidate(self, keys: list[str] = None):
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
        from rich.console import Console

        from plextraktsync.rich.RichHighlighter import RichHighlighter

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

        return PlexApi(
            server=self.plex_server,
            config=self.server_config,
        )

    @cached_property
    def media_factory(self):
        from plextraktsync.media.MediaFactory import MediaFactory

        trakt = self.trakt_api
        plex = self.plex_api
        mf = MediaFactory(plex, trakt)

        return mf

    def get_plex_by_id(self, server_id: str):
        server_config = self.server_config_factory.server_by_id(server_id)
        if server_config is not None and server_config is not self.server_config:
            self.invalidate(["plex_api", "plex_server", "server_config"])
            self.run_config.server = server_config.name

        return self.plex_api

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
    def plex_lists(self):
        from plextraktsync.plex.PlexPlaylistCollection import \
            PlexPlaylistCollection

        return PlexPlaylistCollection(self.plex_server)

    @cached_property
    def has_plex_token(self):
        try:
            return self.server_config.token is not None
        except RuntimeError:
            return False

    @cached_property
    def server_config_factory(self):
        from plextraktsync.config.ServerConfigFactory import \
            ServerConfigFactory

        return ServerConfigFactory()

    @cached_property
    def server_config(self):

        config = self.config
        run_config = self.run_config
        server_config = self.server_config_factory
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
            cache_control=True,
            urls_expire_after=urls_expire_after,
        )

    @cached_property
    def sync(self):
        from plextraktsync.sync.Sync import Sync

        plex = self.plex_api
        trakt = self.trakt_api

        return Sync(self.sync_config, plex, trakt)

    @cached_property
    def progressbar(self):
        if not self.run_config.progressbar:
            return None

        from functools import partial

        from plextraktsync.rich.RichProgressBar import RichProgressBar

        return partial(RichProgressBar, options={"console": self.console})

    @cached_property
    def run_config(self):
        from plextraktsync.config.RunConfig import RunConfig

        config = RunConfig()

        return config

    @cached_property
    def walk_config(self):
        from plextraktsync.plan.WalkConfig import WalkConfig

        wc = WalkConfig()

        return wc

    @cached_property
    def plex_audio_codec(self):
        from plextraktsync.plex.PlexAudioCodec import PlexAudioCodec

        return PlexAudioCodec()

    @cached_property
    def walker(self):
        from plextraktsync.plan.Walker import Walker

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

        from plextraktsync.logger.init import initialize

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
        from rich.logging import RichHandler

        from plextraktsync.rich.RichHighlighter import RichHighlighter

        config = self.config
        handler = RichHandler(
            console=self.console,
            show_time=config.log_console_time,
            log_time_format="[%Y-%m-%d %X]",
            show_path=False,
            highlighter=RichHighlighter(),
            rich_tracebacks=True,
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

    @property
    def sync_config(self):
        from plextraktsync.config.SyncConfig import SyncConfig

        return SyncConfig(self.config, self.server_config)

    @cached_property
    def queue(self):
        from plextraktsync.queue.BackgroundTask import BackgroundTask
        from plextraktsync.queue.Queue import Queue
        from plextraktsync.queue.TraktBatchWorker import TraktBatchWorker
        from plextraktsync.queue.TraktMarkWatchedWorker import \
            TraktMarkWatchedWorker
        from plextraktsync.queue.TraktScrobbleWorker import TraktScrobbleWorker

        workers = [
            TraktBatchWorker(),
            TraktMarkWatchedWorker(),
            TraktScrobbleWorker(),
        ]
        task = BackgroundTask(self.batch_delay_timer, *workers)
        queue = Queue(task)

        return queue

    @cached_property
    def batch_delay_timer(self):
        from plextraktsync.util.Timer import Timer

        return Timer(self.run_config.batch_delay) if self.run_config.batch_delay else None
