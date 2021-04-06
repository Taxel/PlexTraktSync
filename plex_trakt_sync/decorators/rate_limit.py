from functools import wraps
from time import sleep, time
from trakt.errors import RateLimitException
from plex_trakt_sync.logging import logger

last_time = None


# https://trakt.docs.apiary.io/#introduction/rate-limiting
def rate_limit(retries=5, delay=None):
    """

    :param retries: number of retries
    :param delay: delay in sec between trakt requests to respect rate limit
    :return:
    """

    def respect_trakt_rate():
        if delay is None:
            return

        global last_time
        if last_time is None:
            last_time = time()
            return

        diff_time = time() - last_time
        if diff_time < delay:
            wait = delay - diff_time
            logger.warning(
                f'Sleeping for {wait:.3f} seconds'
            )
            sleep(wait)
        last_time = time()

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            retry = 0
            while True:
                try:
                    respect_trakt_rate()
                    return fn(*args, **kwargs)
                except RateLimitException as e:
                    if retry == retries:
                        raise e

                    seconds = int(e.response.headers.get("Retry-After", 1))
                    retry += 1
                    logger.warning(
                        f'RateLimitException for {fn}, retrying after {seconds} seconds (try: {retry}/{retries})'
                    )
                    sleep(seconds)

        return wrapper

    return decorator
