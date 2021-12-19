from functools import wraps


def flatten(method):
    @wraps(method)
    def inner(*args):
        return list(method(*args))

    return inner
