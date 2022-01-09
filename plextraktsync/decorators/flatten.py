from functools import wraps


def flatten_list(method):
    @wraps(method)
    def inner(*args, **kwargs):
        return list(method(*args, **kwargs))

    return inner


def flatten_dict(method):
    @wraps(method)
    def inner(*args, **kwargs):
        return dict(method(*args, **kwargs))

    return inner
