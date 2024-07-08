from __future__ import annotations

from plextraktsync.factory import factory
from plextraktsync.path import cache_dir, config_dir, log_dir, servers_config


def info(print=factory.print):
    version = factory.version
    print(f"PlexTraktSync Version: {version.full_version}")

    print(f"Python Version: {version.py_full_version}")
    print(f"Plex API Version: {version.plex_api_version}")
    print(f"Trakt API Version: {version.trakt_api_version}")
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

    if factory.has_plex_token:
        plex = factory.plex_api
        print(f"Plex Server version: {plex.version}, updated at: {plex.updated_at}")

        sections = plex.library_sections
        print(f"Enabled {len(sections.keys())} libraries in Plex Server:")
        for id, section in sorted(sections.items()):
            print(f" - {id}: {section.title_link}")
