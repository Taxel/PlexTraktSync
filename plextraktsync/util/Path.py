from os import getenv, makedirs
from os.path import abspath, dirname, exists, join

from plextraktsync.decorators.cached_property import cached_property


class Path:
    def __init__(self):
        self.app_name = "PlexTraktSync"
        self.module_path = dirname(dirname(abspath(__file__)))
        self.app_path = dirname(self.module_path)

        self.ensure_dir(self.config_dir)
        self.ensure_dir(self.log_dir)
        self.ensure_dir(self.cache_dir)

        self.default_config_file = join(self.module_path, "config.default.yml")
        self.default_servers_file = join(self.module_path, "servers.default.yml")
        self.config_file = join(self.config_dir, "config.json")
        self.config_yml = join(self.config_dir, "config.yml")
        self.servers_config = join(self.config_dir, "servers.yml")
        self.pytrakt_file = join(self.config_dir, ".pytrakt.json")
        self.env_file = join(self.config_dir, ".env")

    @cached_property
    def config_dir(self):
        d = self.app_dir.user_config_dir if self.installed else self.app_path
        return getenv("PTS_CONFIG_DIR", d)

    @cached_property
    def cache_dir(self):
        d = self.app_dir.user_cache_dir if self.installed else self.app_path
        return getenv("PTS_CACHE_DIR", d)

    @cached_property
    def log_dir(self):
        d = self.app_dir.user_log_dir if self.installed else self.app_path
        return getenv("PTS_LOG_DIR", d)

    @cached_property
    def app_dir(self):
        from appdirs import AppDirs

        return AppDirs(self.app_name)

    @cached_property
    def installed(self):
        from plextraktsync.util.packaging import installed

        return installed()

    @staticmethod
    def ensure_dir(directory):
        if not exists(directory):
            makedirs(directory)
