from functools import partial
from typing import List

import plexapi.server

from plextraktsync.config import PLEX_PLATFORM
from plextraktsync.decorators.nocache import nocache
from plextraktsync.factory import Factory
from plextraktsync.logging import logger


class PlexServerConnection:
    def __init__(self, factory: Factory):
        self.factory = factory

    @property
    def timeout(self):
        return self.factory.config()["plex"]["timeout"]

    @property
    def session(self):
        return self.factory.session()

    @nocache
    def connect(self, urls: List[str], token: str):
        plexapi.X_PLEX_PLATFORM = PLEX_PLATFORM
        plexapi.TIMEOUT = self.timeout
        plexapi.BASE_HEADERS["X-Plex-Platform"] = plexapi.X_PLEX_PLATFORM

        PlexServer = partial(plexapi.server.PlexServer, session=self.session)

        # if connection fails, it will try:
        # 1. url expected by new ssl certificate
        # 2. url without ssl
        # 3. local url (localhost)
        for url in urls:
            try:
                return PlexServer(token=token, baseurl=url)
            except plexapi.server.requests.exceptions.SSLError as e:
                logger.error(e)
                message = str(e.__context__)

                # 1.
                # HTTPSConnectionPool(host='127.0.0.1', port=32400):
                # Max retries exceeded with url: / (
                #  Caused by SSLError(
                #   CertificateError(
                #     "hostname '127.0.0.1' doesn't match '*.5125cc430e5f1919c27226507eab90df.plex.direct'"
                #    )
                #  )
                # )
                if "doesn't match '*." in message and ".plex.direct" in url:
                    url = self.extract_plex_direct(url, message)
                    logger.warning(f"Trying with url: {url}")
                    urls.append(url)
                    continue
                logger.error(e)

            except Exception as e:
                logger.error(e)
                # 2.
                if url[:5] == "https":
                    url = url.replace("https", "http")
                    logger.warning(f"Trying with url: {url}")
                    urls.append(url)
                    continue

        logger.error("No more methods to connect. Giving up.")
        exit(1)

    @staticmethod
    def extract_plex_direct(url: str, message: str):
        """
        Extract .plex.direct url from message.
        The url must be with .plex.direct domain.
        """
        hash_pos = message.find("*.") + 2
        hash_value = message[hash_pos:hash_pos + 32]
        end_pos = url.find(".plex.direct")

        return url[: end_pos - 32] + hash_value + url[end_pos:]


def get_plex_server():
    from plextraktsync.factory import factory
    config = factory.config()

    return PlexServerConnection(factory).connect(
        urls=[
            config["PLEX_BASEURL"],
            config["PLEX_LOCALURL"],
        ],
        token=config["PLEX_TOKEN"]
    )
