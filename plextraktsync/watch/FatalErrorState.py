from __future__ import annotations

from threading import Lock


class FatalErrorState:
    def __init__(self):
        self._error = None
        self._lock = Lock()

    def clear(self):
        with self._lock:
            self._error = None

    def set(self, error: Exception):
        with self._lock:
            if self._error is None:
                self._error = error

    def raise_if_set(self):
        with self._lock:
            error = self._error

        if error is not None:
            raise error
