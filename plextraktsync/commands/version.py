import sys

import click
from plexapi import VERSION as PLEX_API_VERSION
from trakt import __version__ as TRAKT_API_VERSION

from plextraktsync.path import cache_dir, config_dir, log_dir
from plextraktsync.version import version as get_version


@click.command()
def version():
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
