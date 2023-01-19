

from plextraktsync.commands.plex_login import plex_login_autoconfig
from plextraktsync.commands.trakt_login import (has_trakt_token,
                                                trakt_login_autoconfig)
from plextraktsync.factory import factory
from plextraktsync.style import highlight, success


def ensure_login():
    if not factory.has_plex_token:
        plex_login_autoconfig()

    if not has_trakt_token():
        trakt_login_autoconfig()


def login():
    print = factory.print

    print(highlight("Checking Plex and Trakt login credentials existence"))
    print("")
    print("It will not test if the credentials are valid, only that they are present.")
    print('If you need to re-login use "plex-login" or "trakt-login" commands respectively.')
    print("")
    ensure_login()
    print(success("Done!"))
