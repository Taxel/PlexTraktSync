import sys

import click
from plexapi import VERSION as PLEX_API_VERSION
from trakt import __version__ as TRAKT_API_VERSION

from plex_trakt_sync.__init__ import __version__ as PTS_VERSION
from plex_trakt_sync.path import cache_dir, config_dir, log_dir
from plex_trakt_sync.version import git_version_info


@click.command()
def version():
    """
    Print application and environment version info
    """

    print(f"PlexTraktSync Version: {PTS_VERSION}")

    git_version = git_version_info()
    if git_version:
        print(f"PlexTraktSync Git Version: [{git_version}]")

    py_version = sys.version.replace("\n", "")
    print(f"Python Version: {py_version}")
    print(f"Plex API Version: {PLEX_API_VERSION}")
    print(f"Trakt API Version: {TRAKT_API_VERSION}")
    print(f"Cache Dir: {cache_dir}")
    print(f"Config Dir: {config_dir}")
    print(f"Log Dir: {log_dir}")
