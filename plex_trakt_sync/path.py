import site
from os import getenv
from os.path import abspath, dirname, join


class Path:
    def __init__(self):
        self.module_path = dirname(abspath(__file__))
        self.app_path = dirname(self.module_path)

        self.default_config_file = join(self.module_path, "config.default.json")
        self.config_file = join(self.config_dir, "config.json")
        self.pytrakt_file = join(self.config_dir, ".pytrakt.json")
        self.env_file = join(self.config_dir, ".env")
        self.log_file = join(self.log_dir, "last_update.log")

    @property
    def config_dir(self):
        return getenv("PTS_CONFIG_DIR", self.app_path)

    @property
    def cache_dir(self):
        return getenv("PTS_CACHE_DIR", self.app_path)

    @property
    def log_dir(self):
        return getenv("PTS_LOG_DIR", self.app_path)


p = Path()

default_config_file = p.default_config_file
config_file = p.config_file
pytrakt_file = p.pytrakt_file
env_file = p.env_file
log_file = p.log_file
cache_dir = p.cache_dir
