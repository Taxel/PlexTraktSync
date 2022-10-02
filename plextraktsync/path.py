from os import getenv, makedirs
from os.path import abspath, dirname, exists, join

from plextraktsync.decorators.cached_property import cached_property


class Path:
    def __init__(self):
        self.app_name = "PlexTraktSync"
        self.module_path = dirname(abspath(__file__))
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


p = Path()

cache_dir = p.cache_dir
config_dir = p.config_dir
log_dir = p.log_dir

default_config_file = p.default_config_file
default_servers_file = p.default_servers_file
config_file = p.config_file
config_yml = p.config_yml
servers_config = p.servers_config
pytrakt_file = p.pytrakt_file
env_file = p.env_file
