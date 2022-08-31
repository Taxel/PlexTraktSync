from dataclasses import dataclass
from os import getenv
from os.path import exists

from dotenv import load_dotenv

from plextraktsync.path import (cache_dir, config_file, config_yml,
                                default_config_file, env_file)

"""
Platform name to identify our application
"""
PLEX_PLATFORM = "PlexTraktSync"

"""
Constant in seconds for how much to wait between Trakt POST API calls.
"""
TRAKT_POST_DELAY = 1.1


@dataclass
class RunConfig:
    """
    Class to hold runtime config parameters
    """

    dry_run: bool = False
    batch_delay: int = 5
    progressbar: bool = True

    def update(self, **kwargs):
        for name, value in kwargs.items():
            self.__setattr__(name, value)

        return self


class ConfigLoader:
    @staticmethod
    def load(path: str):
        if path.endswith('.yml'):
            return ConfigLoader.load_yaml(path)
        if path.endswith('.json'):
            return ConfigLoader.load_json(path)
        raise RuntimeError(f'Unknown file type: {path}')

    @staticmethod
    def write(path: str, config):
        if path.endswith('.yml'):
            return ConfigLoader.write_yaml(path, config)
        if path.endswith('.json'):
            return ConfigLoader.write_json(path, config)
        raise RuntimeError(f'Unknown file type: {path}')

    @staticmethod
    def copy(src: str, dst: str):
        import shutil

        shutil.copyfile(src, dst)

    @staticmethod
    def rename(src: str, dst: str):
        from os import rename

        rename(src, dst)

    @staticmethod
    def load_json(path: str):
        from json import JSONDecodeError, load

        with open(path, "r", encoding="utf-8") as fp:
            try:
                config = load(fp)
            except JSONDecodeError as e:
                raise RuntimeError(f"Unable to parse {path}: {e}")
        return config

    @staticmethod
    def load_yaml(path: str):
        import yaml

        with open(path, "r", encoding="utf-8") as fp:
            try:
                config = yaml.safe_load(fp)
            except yaml.YAMLError as e:
                raise RuntimeError(f"Unable to parse {path}: {e}")
        return config

    @staticmethod
    def write_json(path: str, config):
        import json

        with open(path, "w", encoding="utf-8") as fp:
            fp.write(json.dumps(config, indent=4))

    @staticmethod
    def write_yaml(path: str, config):
        import yaml

        with open(path, "w", encoding="utf-8") as fp:
            yaml.dump(config, fp, allow_unicode=True, indent=2)


class Config(dict):
    env_keys = [
        "PLEX_BASEURL",
        "PLEX_FALLBACKURL",  # legacy, used before 0.18.21
        "PLEX_LOCALURL",
        "PLEX_TOKEN",
        "PLEX_OWNER_TOKEN",
        "PLEX_USERNAME",
        "TRAKT_USERNAME",
    ]

    initialized = False
    config_file = config_file
    config_yml = config_yml
    env_file = env_file

    def __getitem__(self, item):
        if not self.initialized:
            self.initialize()
        return dict.__getitem__(self, item)

    def __contains__(self, item):
        if not self.initialized:
            self.initialize()
        return dict.__contains__(self, item)

    @property
    def log_file(self):
        from os.path import join

        from .path import log_dir

        return join(log_dir, self["logging"]["filename"])

    @property
    def log_debug(self):
        return ("log_debug_messages" in self and self["log_debug_messages"]) or self["logging"]["debug"]

    @property
    def log_append(self):
        return self["logging"]["append"]

    @property
    def log_console_time(self):
        return self["logging"]["console_time"]

    @property
    def cache_path(self):
        return self["cache"]["path"]

    def initialize(self):
        """
        Config load order:
        - load config.defaults.yml
        - if config.json present and config.yml is not:
            - load config.json
            - write config.yml with config.json contents
        - if config.yml is missing, copy config.defaults.yml to it
        - load config.yml, load and merge it
        """
        self.initialized = True

        loader = ConfigLoader()
        defaults = loader.load(default_config_file)
        self.update(defaults)

        if exists(self.config_file) and not exists(self.config_yml):
            config = loader.load(self.config_file)
            loader.write(self.config_yml, config)

            # Rename, so users would not mistakenly edit outdated file
            config_bak = f"{self.config_file}.old"
            from plextraktsync.logging import logger
            logger.warning(f"Renaming {self.config_file} to {config_bak}")
            loader.rename(self.config_file, config_bak)
        else:
            if not exists(self.config_yml):
                loader.copy(default_config_file, self.config_yml)

        config = loader.load(self.config_yml)
        self.merge(config, self)
        override = self["config"]["dotenv_override"]

        load_dotenv(self.env_file, override=override)
        for key in self.env_keys:
            value = getenv(key)
            if value == "-" or value == "None" or value == "":
                value = None
            self[key] = value

        if self["PLEX_LOCALURL"] is None:  # old .env file used before 0.18.21
            self["PLEX_LOCALURL"] = self["PLEX_FALLBACKURL"]
            self["PLEX_FALLBACKURL"] = None

        self["cache"]["path"] = self["cache"]["path"].replace(
            "$PTS_CACHE_DIR", cache_dir
        )

    # https://stackoverflow.com/a/20666342/2314626
    def merge(self, source, destination):
        for key, value in source.items():
            if isinstance(value, dict):
                # get node or create one
                node = destination.setdefault(key, {})
                self.merge(value, node)
            else:
                destination[key] = value

        return destination

    def save(self):
        with open(self.env_file, "w") as txt:
            txt.write("# This is .env file for PlexTraktSync\n")
            for key in self.env_keys:
                if key in self and self[key] is not None:
                    txt.write("{}={}\n".format(key, self[key]))
                else:
                    txt.write("{}=\n".format(key))


CONFIG = Config()
