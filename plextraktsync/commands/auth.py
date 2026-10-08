from __future__ import annotations

import json
from datetime import datetime, timezone
from os.path import exists

from plextraktsync.factory import factory
from plextraktsync.path import pytrakt_file
from plextraktsync.style import error, success


def trakt_token_expiry():
    if not exists(pytrakt_file):
        return None

    try:
        with open(pytrakt_file) as fp:
            expires_at = json.load(fp).get("OAUTH_EXPIRES_AT")
        if not expires_at:
            return None
        return datetime.fromtimestamp(int(expires_at), tz=timezone.utc)
    except (OSError, ValueError, TypeError):
        return None


def print_plex_status(print):
    if not factory.has_plex_token:
        print(error("✗ Plex not authenticated"))
        print('  Run "plex-login" to authenticate.')
        return

    print(success("✓ Plex authenticated"))
    print(f"  Username: {factory.config['PLEX_USERNAME']}")
    print(f"  Server: {factory.server_config.name}")
    try:
        plex = factory.plex_api
        print(f"  Server version: {plex.version}, updated at: {plex.updated_at}")
    except Exception as e:
        print(f"  Unable to get server details: {e}")


def print_trakt_status(print):
    from plextraktsync.commands.trakt_login import has_trakt_token

    if not has_trakt_token():
        print(error("✗ Trakt not authenticated"))
        print('  Run "trakt-login" to authenticate.')
        return

    print(success("✓ Trakt authenticated"))
    try:
        print(f"  Username: {factory.trakt_api.me.username}")
    except Exception as e:
        print(f"  Unable to get username: {e}")

    expires_at = trakt_token_expiry()
    if expires_at:
        print(f"  Token expires at: {expires_at:%Y-%m-%d %H:%M:%S %Z}")


def auth(print=factory.print):
    print_plex_status(print)
    print("")
    print_trakt_status(print)
