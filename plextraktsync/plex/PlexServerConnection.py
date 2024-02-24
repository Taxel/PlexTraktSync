from __future__ import annotations

import plexapi
from click import ClickException
from plexapi.exceptions import Unauthorized
from plexapi.server import PlexServer
from requests.exceptions import ConnectionError, SSLError

from plextraktsync.config import PLEX_PLATFORM
from plextraktsync.decorators.nocache import nocache
from plextraktsync.factory import Factory, logging


class PlexServerConnection:
    logger = logging.getLogger(__name__)

    def __init__(self, factory: Factory):
        self.factory = factory

    @property
    def timeout(self):
        return self.config["plex"]["timeout"]

    @property
    def config(self):
        return self.factory.config

    @property
    def session(self):
        return self.factory.session

    @nocache
    def connect(self, urls: list[str], token: str):
        plexapi.X_PLEX_PLATFORM = PLEX_PLATFORM
        plexapi.TIMEOUT = self.timeout
        plexapi.BASE_HEADERS["X-Plex-Platform"] = plexapi.X_PLEX_PLATFORM

        # if connection fails, it will try:
        # 1. url expected by new ssl certificate
        # 2. url without ssl
        # 3. local url (localhost)
        for url in urls:
            self.logger.info(f"Connecting with url: {url}, timeout {self.timeout} seconds")
            try:
                return PlexServer(baseurl=url, token=token, session=self.session, timeout=self.timeout)
            except SSLError as e:
                self.logger.error(e)
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
                    self.logger.warning(f"Adding rewritten plex.direct url to connect with: {url}")
                    urls.append(url)
                    continue

                self.logger.error(e)

            except ConnectionError as e:
                self.logger.error(e)
                # 2.
                if url and url[:5] == "https":
                    url = url.replace("https", "http")
                    self.logger.warning(f"Adding rewritten http url to connect with: {url}")
                    urls.append(url)
                    continue
            except Unauthorized as e:
                self.logger.error(e)

        raise ClickException("No more methods to connect. Giving up")

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
