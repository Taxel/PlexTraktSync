import json
from os import path

SRC_DIR = path.dirname(path.abspath(__file__))
CONFIG_DIR = path.join(SRC_DIR, '../config/')
LOG_DIR = path.join(SRC_DIR, '../log/')
CACHE_DIR = path.join(SRC_DIR, '../cache/')


config_file = path.join(CONFIG_DIR, "config.json")
with open(config_file, 'r') as fp:
    CONFIG = json.load(fp)