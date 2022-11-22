import sys

from plexapi import VERSION as PLEX_API_VERSION
from trakt import __version__ as TRAKT_API_VERSION

from plextraktsync.commands.plex_login import has_plex_token
from plextraktsync.factory import factory, logger
from plextraktsync.path import cache_dir, config_dir, log_dir, servers_config
from plextraktsync.version import version as get_version


def info(print=logger.info):
    print(f"PlexTraktSync Version: {get_version()}")

    py_version = sys.version.replace("\n", "")
    print(f"Python Version: {py_version}")
    print(f"Plex API Version: {PLEX_API_VERSION}")
    print(f"Trakt API Version: {TRAKT_API_VERSION}")
    print(f"Cache Dir: {cache_dir}")
    print(f"Config Dir: {config_dir}")
    print(f"Log Dir: {log_dir}")

    config = factory.config
    print(f"Log File: {config.log_file}")
    print(f"Cache File: {config.cache_path}.sqlite")
    print(f"Config File: {config.config_yml}")
    print(f"Servers Config File: {servers_config}")

    print(f"Plex username: {config['PLEX_USERNAME']}")
    print(f"Trakt username: {config['TRAKT_USERNAME']}")

    print(f"Plex Server Name: {factory.server_config.name}")

    if has_plex_token():
        plex = factory.plex_api
        print(f"Plex Server version: {plex.version}, updated at: {plex.updated_at}")
        print(
            f"Enabled {len(plex.library_sections)} libraries in Plex Server: {plex.library_section_names}"
        )
