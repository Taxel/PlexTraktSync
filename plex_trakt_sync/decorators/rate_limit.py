from functools import wraps
from time import sleep

from requests.exceptions import ConnectionError
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
                except (RateLimitException, ConnectionError, TraktInternalException) as e:
                    if retry == retries:
                        raise e

                    if isinstance(e, RateLimitException):
                        seconds = int(e.response.headers.get("Retry-After", 1))
                    else:
                        seconds = 1 + retry
                    retry += 1
                    logger.warning(
                        f"{e} for {fn}, retrying after {seconds} seconds (try: {retry}/{retries})"
                    )
                    sleep(seconds)

        return wrapper

    return decorator
