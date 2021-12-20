from functools import wraps


def flatten_list(method):
    @wraps(method)
    def inner(*args):
        return list(method(*args))

    return inner


def flatten_dict(method):
    @wraps(method)
    def inner(*args):
        return dict(method(*args))

    return inner
