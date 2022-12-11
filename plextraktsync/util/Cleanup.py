class Cleanup:
    """
    Class that runs cleanups once.
    """

    def __init__(self):
        self.cleanups = set()

    def add(self, cb):
        self.cleanups.add(cb)

    def run(self):
        try:
            for cb in list(self.cleanups):
                cb()
                self.cleanups.remove(cb)
        finally:
            self.cleanups.clear()
