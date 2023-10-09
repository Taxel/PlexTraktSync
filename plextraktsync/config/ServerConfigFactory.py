from os.path import exists

from plextraktsync.config.ConfigLoader import ConfigLoader
from plextraktsync.config.ConfigMergeMixin import ConfigMergeMixin
from plextraktsync.config.PlexServerConfig import PlexServerConfig
from plextraktsync.path import servers_config


class ServerConfigFactory(ConfigMergeMixin):
    config_path = servers_config
    loaded = False

    def __init__(self):
        self.servers = {}

    def get_server(self, name: str):
        self.load()
        try:
            return PlexServerConfig(name=name, **self.servers[name])
        except KeyError:
            raise RuntimeError(f"Server with name {name} is not defined")

    def server_by_id(self, id: str):
        for name, server in self.servers.items():
            if "id" in server and id == server["id"]:
                return self.get_server(name)

    def load(self):
        if self.loaded:
            return self
        self.loaded = True
        loader = ConfigLoader()

        if exists(self.config_path):
            servers = loader.load(self.config_path)
            self.merge(servers["servers"], self.servers)
        else:
            self.migrate()
        return self

    def migrate(self):
        from plextraktsync.factory import factory
        config = factory.config

        if not config["PLEX_BASEURL"]:
            return

        self.add_server(
            name="default",
            urls=[
                config["PLEX_BASEURL"],
                config["PLEX_LOCALURL"],
            ],
            token=config["PLEX_TOKEN"],
        )
        self.save()
        config["PLEX_SERVER"] = "default"
        config.save()

        logger = factory.logger
        logger.warning(f"Added default server to {self.config_path}")

    def save(self):
        loader = ConfigLoader()
        loader.write(self.config_path, {
            "servers": self.servers,
        })

    def add_server(self, **kwargs):
        self.load()
        config = PlexServerConfig(**kwargs)
        servers = {
            config.name: config.asdict(),
        }
        self.merge(servers, self.servers)
