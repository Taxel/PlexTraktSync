from os.path import dirname, abspath, join

app_path = dirname(dirname(abspath(__file__)))
config_file = join(app_path, "config.json")
pytrakt_file = join(app_path, ".pytrakt.json")
env_file = join(app_path, ".env")
