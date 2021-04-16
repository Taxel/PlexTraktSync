import json
from dotenv import load_dotenv
from os import getenv
from plex_trakt_sync.path import config_file, env_file, default_config_file
from os.path import exists

"""
Platform name to identify our application
"""
PLEX_PLATFORM = "PlexTraktSync"


class Config(dict):
    env_keys = [
        "PLEX_BASEURL",
        "PLEX_FALLBACKURL",
        "PLEX_TOKEN",
        "PLEX_USERNAME",
        "TRAKT_USERNAME",
    ]

    defaults = {
        "log_debug_messages": False,
        "logging": {
            "append": False,
        },
        "sync": {
            "liked_lists": True,
            "watchlist": True,
            "watched_status": True,
            "collection": True,
            "ratings": True,
        },
        "xbmc-providers": {
            "movies": "imdb",
            "shows": "tvdb",
        },
        "excluded-libraries": [
        ],
    }

    initialized = False

    def __getitem__(self, item):
        if not self.initialized:
            self.initialize()
        return dict.__getitem__(self, item)

    def initialize(self):
        self.update(self.defaults)

        if not exists(config_file):
            with open(default_config_file, "r") as fp:
                defaults = json.load(fp)
            with open(config_file, "w") as fp:
                fp.write(json.dumps(defaults, indent=4))

        with open(config_file, "r") as fp:
            config = json.load(fp)
            self.update(config)

        self.initialized = True

        load_dotenv()
        if not getenv("PLEX_TOKEN") or not getenv("TRAKT_USERNAME"):
            print("First run, please follow those configuration instructions.")
            from get_env_data import get_env_data
            get_env_data()
            load_dotenv()

        for key in self.env_keys:
            self[key] = getenv(key)

    def save(self):
        with open(env_file, "w") as txt:
            txt.write("# This is .env file for PlexTraktSync\n")
            for key in self.env_keys:
                if key in self:
                    txt.write("{}={}\n".format(key, self[key]))
                else:
                    txt.write("{}=\n".format(key))


CONFIG = Config()
