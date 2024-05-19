from __future__ import annotations

import atexit
from queue import SimpleQueue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


class Queue:
    def __init__(self, runner):
        self.queue = SimpleQueue()
        self.daemon = self.start_daemon(runner)
        atexit.register(self.close)

    def add_to_collection(self, data):
        self.add_queue("add_to_collection", data)

    def remove_from_collection(self, data):
        self.add_queue("remove_from_collection", data)

    def add_to_watchlist(self, data):
        self.add_queue("add_to_watchlist", data)

    def remove_from_watchlist(self, data):
        self.add_queue("remove_from_watchlist", data)

    def add_to_history(self, data):
        self.add_queue("add_to_history", data)

    def scrobble_update(self, data):
        self.add_queue("scrobble_update", data)

    def scrobble_pause(self, data):
        self.add_queue("scrobble_pause", data)

    def scrobble_stop(self, data):
        self.add_queue("scrobble_stop", data)

    def add_queue(self, queue: str, data: Any):
        """
        Add "data" to "queue". Returns immediately
        """
        self.queue.put((queue, data))

    def start_daemon(self, runner):
        from threading import Thread

        daemon = Thread(
            target=runner, args=(self.queue,), daemon=True, name="BackgroundTask"
        )
        daemon.start()

        return daemon

    def close(self):
        """
        Close queue.
        Terminate child thread and stop accepting items to queue.
        """
        if self.daemon.is_alive():
            self.queue.put(None)
            self.daemon.join()
        self.queue = None
