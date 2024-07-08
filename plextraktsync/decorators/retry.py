from __future__ import annotations

from time import sleep

from click import ClickException
from decorator import decorator
from plexapi.exceptions import BadRequest
from requests import ReadTimeout, RequestException
from trakt.errors import (
    BadResponseException,
    TraktBadGateway,
    TraktInternalException,
    TraktUnavailable,
)

from plextraktsync.factory import logging

logger = logging.getLogger(__name__)


@decorator
def retry(fn, retries=5, *args, **kwargs):
    count = 0
    while True:
        try:
            return fn(*args, **kwargs)
        except (
            BadRequest,
            BadResponseException,
            ReadTimeout,
            RequestException,
            TraktBadGateway,
            TraktUnavailable,
            TraktInternalException,
        ) as e:
            if count == retries:
                logger.error(f"Error: {e}")

                if isinstance(e, BadResponseException):
                    logger.error(f"Details: {e.details}")
                if isinstance(e, TraktInternalException):
                    logger.error(f"Error message: {e.error_message}")

                logger.error(f"Last call: {fn.__module__}.{fn.__name__}({args[1:]}, {kwargs})")
                raise ClickException("API didn't respond properly, script will abort now. Please try again later.")

            seconds = 1 + count
            count += 1
            logger.warning(f"{e} for {fn.__module__}.{fn.__name__}(), retrying after {seconds} seconds (try: {count}/{retries})")
            sleep(seconds)
