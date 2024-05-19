from decorator import decorator


@decorator
def flatten_list(method, *args, **kwargs):
    return list(method(*args, **kwargs))


@decorator
def flatten_dict(method, *args, **kwargs):
    return dict(method(*args, **kwargs))


@decorator
def flatten_set(method, *args, **kwargs):
    return set(method(*args, **kwargs))
