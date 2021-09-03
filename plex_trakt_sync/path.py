from os import getenv
from os.path import abspath, dirname, join

app_path = dirname(dirname(abspath(__file__)))

PTS_CONFIG_DIR = getenv("PTS_CONFIG_DIR", app_path)
PTS_CACHE_DIR = getenv("PTS_CACHE_DIR", app_path)
PTS_LOG_DIR = getenv("PTS_LOG_DIR", app_path)

default_config_file = join(app_path, "config.default.json")
config_file = join(PTS_CONFIG_DIR, "config.json")
pytrakt_file = join(PTS_CONFIG_DIR, ".pytrakt.json")
env_file = join(PTS_CONFIG_DIR, ".env")
log_file = join(PTS_LOG_DIR, "last_update.log")
