from functools import wraps
from time import sleep

from requests import RequestException
from trakt.errors import RateLimitException, TraktInternalException
from plex_trakt_sync.logging import logger


# https://trakt.docs.apiary.io/#introduction/rate-limiting
def rate_limit(retries=5):
    """
    :param retries: number of retries
    :return:
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            retry = 0
            while True:
                try:
                    return fn(*args, **kwargs)
                except (RateLimitException, RequestException, TraktInternalException) as e:
                    if retry == retries:
                        logger.error(f"Error: {e}")
                        logger.error(f"API didn't respond properly, script will abort now. Please try again later.")
                        exit(1)

                    if isinstance(e, RateLimitException):
                        seconds = int(e.response.headers.get("Retry-After", 1))
                    else:
                        seconds = 1 + retry
                    retry += 1
                    logger.warning(
                        f"{e} for {fn.__module__}.{fn.__name__}(), retrying after {seconds} seconds (try: {retry}/{retries})"
                    )
                    sleep(seconds)

        return wrapper

    return decorator
