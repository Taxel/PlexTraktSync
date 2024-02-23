from functools import wraps
from time import sleep

from click import ClickException
from trakt.errors import RateLimitException

from plextraktsync.factory import logging

logger = logging.getLogger(__name__)


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
                except RateLimitException as e:
                    if retry == retries:
                        logger.error(f"Trakt Error: {e}")
                        logger.error(
                            f"Last call: {fn.__module__}.{fn.__name__}({args[1:]}, {kwargs})"
                        )
                        raise ClickException(
                            "Trakt API didn't respond properly, script will abort now. Please try again later."
                        )

                    seconds = e.retry_after
                    retry += 1
                    logger.warning(
                        f"{e} for {fn.__module__}.{fn.__name__}(), retrying after {seconds} seconds (try: {retry}/{retries})"
                    )
                    logger.debug(e.details)
                    sleep(seconds)

        return wrapper

    return decorator
