from time import monotonic, sleep

from plextraktsync.factory import logging


class Timer:
    """
    Class dealing with limiting that something is not called more often than {delay}
    """

    def __init__(self, delay: float):
        if delay <= 0:
            raise ValueError(f"Delay must be a positive number: {delay}")
        self.delay = delay
        self.last_time = None
        self.logger = logging.getLogger("PlexTraktSync.Timer")

    @property
    def time_remaining(self):
        last_time = self.last_time
        if not last_time:
            return 0.0
        diff_time = monotonic() - last_time
        if diff_time < self.delay:
            return self.delay - diff_time
        return 0.0

    def update(self):
        self.last_time = monotonic()

    def start(self):
        """
        Start the timer only if not yet started
        """
        if not self.last_time:
            self.update()

    def wait_if_needed(self):
        if not self.last_time:
            self.update()
            return

        wait = self.time_remaining
        if wait:
            self.logger.debug(f"Sleeping for {wait:.3f} seconds")
            sleep(wait)
        self.update()
