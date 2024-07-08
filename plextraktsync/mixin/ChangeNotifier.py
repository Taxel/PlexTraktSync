from __future__ import annotations


class ChangeNotifier(dict):
    """
    MixIn that would make dict object notify listeners when a value is set to dict
    """

    listeners = []

    def add_listener(self, listener, keys=None):
        self.listeners.append((listener, keys))

    def notify(self, key, value):
        for listener, keys in self.listeners:
            if keys is not None and key not in keys:
                continue
            listener(key, value)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.notify(key, value)
