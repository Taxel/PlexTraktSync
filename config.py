import json
from plex_trakt_sync.path import config_file

with open(config_file, 'r') as fp:
    CONFIG = json.load(fp)