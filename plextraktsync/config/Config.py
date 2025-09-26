from __future__ import annotations

from os import getenv
from os.path import exists

from dotenv import load_dotenv

from plextraktsync.config.ConfigLoader import ConfigLoader
from plextraktsync.config.ConfigMergeMixin import ConfigMergeMixin
from plextraktsync.mixin.ChangeNotifier import ChangeNotifier
from plextraktsync.path import (
    cache_dir,
    config_file,
    config_yml,
    default_config_file,
    env_file,
)


class Config(ChangeNotifier, ConfigMergeMixin, dict):
    # Value other than True adds a note to the env key to written .env
    env_keys = {
        "PLEX_USERNAME": True,
        "TRAKT_USERNAME": True,
        "PLEX_SERVER": True,  # new in 0.24.0
        # The token of the PMS administrator/owner.
        # This is stored/used only for managed users (home users) so the script
        # can get their watchlist from Plex online servers. Managed users don't
        # have a Plex account, they're local users.
        "PLEX_OWNER_TOKEN": True,
        # The account token of the Plex user who have a Plex account but don't
        # own the PMS (use it as shared library).
        # This is stored/used only if user uses a shared PMS.
        # Needed to fetch its watchlist from Plex online servers.
        "PLEX_ACCOUNT_TOKEN": True,
        # Old keys, Do not write to .env anymore
        "PLEX_FALLBACKURL": False,
        "PLEX_BASEURL": False,
        "PLEX_LOCALURL": False,
        "PLEX_TOKEN": False,
    }

    initialized = False
    config_file = config_file
    config_yml = config_yml
    env_file = env_file

    def __init__(self, config_file=None):
        super().__init__()
        if config_file:
            self.config_yml = config_file

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

        from ..path import log_dir

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
    def log_rotation(self):
        return self["logging"]["rotation"]["enable"]

    @property
    def log_rotation_max_bytes(self):
        return self["logging"]["rotation"]["max_bytes"]

    @property
    def log_rotation_backup_count(self):
        return self["logging"]["rotation"]["backup_count"]

    @property
    def cache_path(self):
        return self["cache"]["path"]

    @property
    def http_cache(self):
        from plextraktsync.config.HttpCacheConfig import HttpCacheConfig

        cache = self["http_cache"] if "http_cache" in self and self["http_cache"] else {"policy": {}}

        return HttpCacheConfig(**cache)

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
            from plextraktsync.factory import factory

            logger = factory.logger
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

        self["cache"]["path"] = self["cache"]["path"].replace("$PTS_CACHE_DIR", cache_dir)

    def serialize(self):
        """
        Print config serialized as yaml.
        If print is None, return the produced string instead.
        """
        data = dict(self)
        # Remove env variables. They are usually secrets
        for key in self.env_keys:
            del data[key]
        return data

    def dump(self, print=None):
        data = self.serialize()
        dump = ConfigLoader.dump_yaml(None, data)
        if print is None:
            return dump
        print(dump)

    def save(self):
        with open(self.env_file, "w") as txt:
            txt.write("# This is .env file for PlexTraktSync\n")
            for key, value in self.env_keys.items():
                if value is False:
                    # Skip the item
                    continue

                if value is not True:
                    # Include deprecation message
                    txt.write(f"# {key}: {value}\n")

                if key in self and self[key] is not None:
                    txt.write(f"{key}={self[key]}\n")
                else:
                    txt.write(f"{key}=\n")
