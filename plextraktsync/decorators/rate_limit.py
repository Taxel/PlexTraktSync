from __future__ import annotations

from time import sleep

from click import ClickException
from decorator import decorator
from trakt.errors import AccountLimitExceeded, RateLimitException

from plextraktsync.factory import logging

logger = logging.getLogger(__name__)


# https://trakt.docs.apiary.io/#introduction/rate-limiting
@decorator
def rate_limit(fn, retries=5, *args, **kwargs):
    retry = 0
    while True:
        try:
            return fn(*args, **kwargs)
        except (RateLimitException, AccountLimitExceeded) as e:
            if isinstance(e, AccountLimitExceeded):
                logger.error(f"Trakt Error: {e}")
                logger.error(f"Trakt Limit: {e.account_limit}")
                logger.error(f"Trakt Details: {e.details}")
                logger.error(f"Trakt headers: {e.response.headers}")
                logger.error(f"Trakt content: {e.response.content}")
                raise ClickException("Skip Retry")

            if retry == retries:
                logger.error(f"Trakt Error: {e}")
                logger.error(f"Last call: {fn.__module__}.{fn.__name__}({args[1:]}, {kwargs})")
                raise ClickException("Trakt API didn't respond properly, script will abort now. Please try again later.")

            seconds = e.retry_after
            retry += 1
            logger.warning(f"{e} for {fn.__module__}.{fn.__name__}(), retrying after {seconds} seconds (try: {retry}/{retries})")
            logger.debug(e.details)
            raise ClickException("Skip Retry")
            sleep(seconds)
