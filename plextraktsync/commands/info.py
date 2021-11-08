import sys

import click
from plexapi import VERSION as PLEX_API_VERSION
from trakt import __version__ as TRAKT_API_VERSION

from plextraktsync.commands.plex_login import has_plex_token
from plextraktsync.factory import factory
from plextraktsync.path import cache_dir, config_dir, log_dir
from plextraktsync.version import version as get_version


@click.command()
def info():
    """
    Print application and environment version info
    """

    print(f"PlexTraktSync Version: {get_version()}")

    py_version = sys.version.replace("\n", "")
    print(f"Python Version: {py_version}")
    print(f"Plex API Version: {PLEX_API_VERSION}")
    print(f"Trakt API Version: {TRAKT_API_VERSION}")
    print(f"Cache Dir: {cache_dir}")
    print(f"Config Dir: {config_dir}")
    print(f"Log Dir: {log_dir}")

    config = factory.config()
    print(f"Plex username: {config['PLEX_USERNAME']}")
    print(f"Trakt username: {config['TRAKT_USERNAME']}")

    if has_plex_token():
        plex = factory.plex_api()
        print(f"Plex Server version: {plex.version}, updated at: {plex.updated_at}")
        print(f"Enabled {len(plex.library_sections)} libraries in Plex Server: {plex.library_section_names}")
