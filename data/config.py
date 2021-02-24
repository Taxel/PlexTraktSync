import json
from os import path

config_file = path.join(path.dirname(path.abspath(__file__)), "config.json")
with open(config_file, 'r') as fp:
    CONFIG = json.load(fp)
