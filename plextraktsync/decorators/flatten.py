from functools import wraps


def flatten_list(method):
    @wraps(method)
    def inner(*args):
        return list(method(*args))

    return inner
