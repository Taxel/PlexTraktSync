from os.path import abspath, dirname, join

app_path = dirname(dirname(abspath(__file__)))
default_config_file = join(app_path, "config.default.json")
config_file = join(app_path, "config.json")
pytrakt_file = join(app_path, ".pytrakt.json")
env_file = join(app_path, ".env")
log_file = join(app_path, "last_update.log")
trakt_cache = join(app_path, "trakt_cache")
