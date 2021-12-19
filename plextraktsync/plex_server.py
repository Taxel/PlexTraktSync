from functools import partial

import plexapi.server

from plextraktsync.config import PLEX_PLATFORM
from plextraktsync.decorators.nocache import nocache
from plextraktsync.factory import factory
from plextraktsync.logging import logger


class PlexServerConnection:
    @staticmethod
    @nocache
    def connect():
        return _get_plex_server()


def get_plex_server():
    return PlexServerConnection().connect()


def _get_plex_server():
    CONFIG = factory.config()
    plex_token = CONFIG["PLEX_TOKEN"]
    plex_baseurl = CONFIG["PLEX_BASEURL"]
    plex_fallbackurl = CONFIG["PLEX_FALLBACKURL"]
    if plex_token == '-':
        plex_token = ""
    server = None

    plexapi.X_PLEX_PLATFORM = PLEX_PLATFORM
    plexapi.BASE_HEADERS['X-Plex-Platform'] = plexapi.X_PLEX_PLATFORM

    session = factory.session()
    PlexServer = partial(plexapi.server.PlexServer, session=session)

    # if connection fails, it will try :
    # 1. url expected by new ssl certificate
    # 2. url without ssl
    # 3. fallback url (localhost)

    try:
        server = PlexServer(token=plex_token, baseurl=plex_baseurl)
    except plexapi.server.requests.exceptions.SSLError as e:
        m = "Plex connection error: {}, fallback url {} didn't respond either.".format(str(e), plex_fallbackurl)
        excep_msg = str(e.__context__)
        if "doesn't match '*." in excep_msg:
            hash_pos = excep_msg.find("*.") + 2
            new_hash = excep_msg[hash_pos:hash_pos + 32]
            end_pos = plex_baseurl.find(".plex.direct")
            new_plex_baseurl = plex_baseurl[:end_pos - 32] + new_hash + plex_baseurl[end_pos:]
            try:  # 1
                server = PlexServer(token=plex_token, baseurl=new_plex_baseurl)
                # save new url to .env
                CONFIG["PLEX_TOKEN"] = plex_token
                CONFIG["PLEX_BASEURL"] = new_plex_baseurl
                CONFIG["PLEX_FALLBACKURL"] = plex_fallbackurl
                CONFIG.save()
                logger.info("Plex server url changed to {}".format(new_plex_baseurl))
            except Exception:
                pass
        if server is None and plex_baseurl[:5] == "https":
            new_plex_baseurl = plex_baseurl.replace("https", "http")
            try:  # 2
                server = PlexServer(token=plex_token, baseurl=new_plex_baseurl)
                logger.warning("Switched to Plex unsecure connection because of SSLError.")
            except Exception:
                pass
    except Exception as e:
        m = "Plex connection error: {}, fallback url {} didn't respond either.".format(str(e), plex_fallbackurl)
    if server is None:
        try:  # 3
            server = PlexServer(token=plex_token, baseurl=plex_fallbackurl)
            logger.warning("No response from {}, fallback to {}".format(plex_baseurl, plex_fallbackurl))
        except Exception:
            logger.error(m)
            print(m)
            exit(1)
    return server
