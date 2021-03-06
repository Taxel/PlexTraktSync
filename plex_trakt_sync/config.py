import json
from plex_trakt_sync.path import config_file


class Config(dict):
    initialized = False

    def __getitem__(self, item):
        if not self.initialized:
            self.initialize()
        return dict.__getitem__(self, item)

    def initialize(self):
        with open(config_file, "r") as fp:
            config = json.load(fp)
            self.update(config)
        self.initialized = True


CONFIG = Config()