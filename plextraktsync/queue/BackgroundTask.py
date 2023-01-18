from __future__ import annotations

from collections import defaultdict
from queue import Empty
from typing import TYPE_CHECKING

from plextraktsync.factory import logging

if TYPE_CHECKING:
    from queue import SimpleQueue
    from typing import Any

    from plextraktsync.util.Timer import Timer


class BackgroundTask:
    """
    Class to read events from queue and invoke them at tasks to flush them at interval set by the timer
    """

    def __init__(self, timer: Timer = None, *tasks):
        self.queues = defaultdict(list)
        self.timer = timer
        self.tasks = tasks
        self.logger = logging.getLogger("PlexTraktSync.BackgroundTask")

    def check_timer(self):
        if not self.timer:
            return

        self.timer.start()
        if self.timer.time_remaining:
            return

        self.timed_events()
        self.timer.update()

    def timed_events(self):
        for task in self.tasks:
            try:
                task(self.queues)
            except Exception as e:
                self.logger.error(f"Got exception while working on {task}: {e}")

    def process_message(self, message: (str, Any)):
        (queue, data) = message
        self.queues[queue].append(data)

    def shutdown(self):
        """
        The shutdown handler: run timed events now.
        """
        self.logger.debug("Shutdown, run timed events now")
        self.timed_events()

    def __call__(self, queue: SimpleQueue):
        """
        Process events from queue and invoke timed events.
        """

        while True:
            try:
                message = queue.get(timeout=1)
            except Empty:
                pass
            else:
                if message is None:
                    self.shutdown()
                    break
                self.process_message(message)

            self.check_timer()
