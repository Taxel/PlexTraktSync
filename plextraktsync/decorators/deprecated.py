try:
    from deprecated import deprecated
except ImportError:
    import warnings
    from functools import wraps


    def deprecated(reason=""):
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                warnings.warn(reason, DeprecationWarning, 2)
                return fn(*args, **kwargs)

            return wrapper

        return decorator
